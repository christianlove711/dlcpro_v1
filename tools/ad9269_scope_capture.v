`timescale 1ns / 1ps

// Low-duty-cycle oscilloscope window generator.
// Two independent 8192x32 simple dual-port block-RAM banks allow capture and
// Scope-DMA transmission to overlap.  The AXIS source deliberately inserts a
// read-latency bubble for payload words so the RAM read is fully synchronous.
module ad9269_scope_capture #(
    parameter integer SAMPLES_PER_FRAME = 8192,
    parameter integer HEADER_WORDS = 16,
    parameter integer CORE_HZ = 100000000
) (
    input  wire        clk,
    input  wire        resetn,
    input  wire        clear,
    input  wire        mode_scope,
    input  wire        armed,
    input  wire        abort,
    input  wire [3:0]  decimation_log2,
    input  wire [1:0]  trigger_mode,
    input  wire        trigger_channel,
    input  wire signed [15:0] trigger_level,
    input  wire        fps_20,
    input  wire [31:0] stream_id,
    input  wire [31:0] sample_rate_hz,
    input  wire        sample_valid,
    input  wire [31:0] sample_pair,
    input  wire [1:0]  sample_otr,
    input  wire [63:0] sample_index,
    output reg  [31:0] scope_data,
    output reg         scope_valid,
    input  wire        scope_ready,
    output reg         scope_last,
    output wire        busy,
    output reg         triggered,
    output reg         overflow,
    output reg [31:0]  frame_count,
    output reg [31:0]  suppressed_count,
    output reg [31:0]  dropped_count
);
  localparam integer PRE_SAMPLES = SAMPLES_PER_FRAME / 4;
  localparam integer POST_SAMPLES = SAMPLES_PER_FRAME - PRE_SAMPLES;
  localparam integer ADDR_W = $clog2(SAMPLES_PER_FRAME);
  localparam integer TOTAL_WORDS = HEADER_WORDS + SAMPLES_PER_FRAME;
  localparam [31:0] MAGIC_SCOP = 32'h504f4353;
  localparam [1:0] SEND_LOAD = 2'd0;
  localparam [1:0] SEND_RAM_WAIT = 2'd1;
  localparam [1:0] SEND_RAM_DATA = 2'd2;
  localparam [1:0] SEND_AXIS = 2'd3;

  (* ram_style = "block" *) reg [31:0] bank0 [0:SAMPLES_PER_FRAME-1];
  (* ram_style = "block" *) reg [31:0] bank1 [0:SAMPLES_PER_FRAME-1];
  reg [31:0] bank0_q;
  reg [31:0] bank1_q;
  reg [ADDR_W-1:0] ram_read_addr;
  reg bank0_write;
  reg bank1_write;
  reg [ADDR_W-1:0] ram_write_addr;
  reg [31:0] ram_write_data;

  // Separate synchronous write/read processes match the Xilinx simple
  // dual-port BRAM inference template.
  always @(posedge clk) begin
    if (bank0_write)
      bank0[ram_write_addr] <= ram_write_data;
  end

  always @(posedge clk) begin
    if (bank1_write)
      bank1[ram_write_addr] <= ram_write_data;
  end

  always @(posedge clk) begin
    bank0_q <= bank0[ram_read_addr];
    bank1_q <= bank1[ram_read_addr];
  end

  reg capture_bank;
  reg bank_ready0;
  reg bank_ready1;
  reg [ADDR_W-1:0] bank_start0;
  reg [ADDR_W-1:0] bank_start1;
  reg [63:0] first_index0;
  reg [63:0] first_index1;
  reg [63:0] trigger_index0;
  reg [63:0] trigger_index1;
  reg [31:0] frame_seq0;
  reg [31:0] frame_seq1;
  reg [31:0] frame_cfg0;
  reg [31:0] frame_cfg1;
  reg [1:0] frame_otr0;
  reg [1:0] frame_otr1;
  reg capture_active;
  reg capture_triggered;
  reg [ADDR_W-1:0] write_ptr;
  reg [ADDR_W:0] accepted_count;
  reg [ADDR_W:0] post_count;
  reg [7:0] decim_count;
  wire [3:0] decim_value =
      (decimation_log2 > 4'd8) ? 4'd8 : decimation_log2;
  reg signed [15:0] previous_sample;
  reg previous_valid;
  reg [31:0] interval_count;
  wire [31:0] interval_limit = fps_20 ? (CORE_HZ/20) : (CORE_HZ/10);
  wire selected_bank_ready = capture_bank ? bank_ready1 : bank_ready0;
  wire signed [15:0] selected_sample =
      trigger_channel ? $signed(sample_pair[31:16]) :
                        $signed(sample_pair[15:0]);
  wire rising_hit = previous_valid && previous_sample < trigger_level &&
                    selected_sample >= trigger_level;
  wire falling_hit = previous_valid && previous_sample > trigger_level &&
                     selected_sample <= trigger_level;
  wire trigger_hit = (trigger_mode == 2'd0) ||
                     (trigger_mode == 2'd1 && rising_hit) ||
                     (trigger_mode == 2'd2 && falling_hit);

  reg send_bank;
  reg send_active;
  reg [1:0] send_state;
  reg [13:0] send_word;
  reg [ADDR_W-1:0] send_start;
  reg [63:0] send_first_index;
  reg [63:0] send_trigger_index;
  reg [31:0] send_frame_seq;
  reg [31:0] send_cfg;
  reg [1:0] send_otr;

  assign busy = capture_active || send_active || bank_ready0 || bank_ready1;

  function [31:0] header_word;
    input [3:0] index;
    begin
      case (index)
        4'd0:  header_word = MAGIC_SCOP;
        4'd1:  header_word = 32'h00010000;
        4'd2:  header_word = stream_id;
        4'd3:  header_word = send_frame_seq;
        4'd4:  header_word = sample_rate_hz;
        4'd5:  header_word = 32'd1 << decim_value;
        4'd6:  header_word = send_first_index[31:0];
        4'd7:  header_word = send_first_index[63:32];
        4'd8:  header_word = send_trigger_index[31:0];
        4'd9:  header_word = send_trigger_index[63:32];
        4'd10: header_word = send_cfg;
        4'd11: header_word = {30'd0, send_otr};
        4'd12: header_word = suppressed_count;
        4'd13: header_word = dropped_count;
        4'd14: header_word = SAMPLES_PER_FRAME;
        default: header_word = HEADER_WORDS * 4;
      endcase
    end
  endfunction

  always @(posedge clk) begin
    if (!resetn || clear || abort) begin
      capture_bank <= 1'b0;
      bank_ready0 <= 1'b0;
      bank_ready1 <= 1'b0;
      capture_active <= 1'b0;
      capture_triggered <= 1'b0;
      write_ptr <= {ADDR_W{1'b0}};
      accepted_count <= 0;
      post_count <= 0;
      decim_count <= 0;
      previous_sample <= 0;
      previous_valid <= 1'b0;
      interval_count <= 0;
      bank0_write <= 1'b0;
      bank1_write <= 1'b0;
      ram_write_addr <= 0;
      ram_write_data <= 0;
      ram_read_addr <= 0;
      send_active <= 1'b0;
      send_state <= SEND_LOAD;
      send_word <= 0;
      scope_data <= 0;
      scope_valid <= 1'b0;
      scope_last <= 1'b0;
      triggered <= 1'b0;
      overflow <= 1'b0;
      frame_count <= 0;
      suppressed_count <= 0;
      dropped_count <= 0;
    end else begin
      bank0_write <= 1'b0;
      bank1_write <= 1'b0;
      triggered <= capture_triggered;

      if (interval_count < interval_limit)
        interval_count <= interval_count + 1'b1;

      if (!mode_scope || !armed) begin
        capture_active <= 1'b0;
        if (interval_count >= interval_limit &&
            suppressed_count != 32'hffff_ffff) begin
          suppressed_count <= suppressed_count + 1'b1;
          interval_count <= 0;
        end
      end else begin
        if (!capture_active && interval_count >= interval_limit) begin
          if (!selected_bank_ready) begin
            capture_active <= 1'b1;
            capture_triggered <= (trigger_mode == 2'd0);
            write_ptr <= 0;
            accepted_count <= 0;
            post_count <= 0;
            interval_count <= 0;
            previous_valid <= 1'b0;
            decim_count <= 0;
            if (capture_bank)
              frame_otr1 <= 0;
            else
              frame_otr0 <= 0;
          end else begin
            overflow <= 1'b1;
            if (dropped_count != 32'hffff_ffff)
              dropped_count <= dropped_count + 1'b1;
            interval_count <= 0;
          end
        end

        if (capture_active && sample_valid) begin
          if (decim_count == ((9'd1 << decim_value) - 1'b1)) begin
            decim_count <= 0;
            ram_write_addr <= write_ptr;
            ram_write_data <= sample_pair;
            if (capture_bank) begin
              bank1_write <= 1'b1;
              frame_otr1 <= frame_otr1 | sample_otr;
            end else begin
              bank0_write <= 1'b1;
              frame_otr0 <= frame_otr0 | sample_otr;
            end
            write_ptr <= write_ptr + 1'b1;
            if (accepted_count < SAMPLES_PER_FRAME)
              accepted_count <= accepted_count + 1'b1;
            previous_sample <= selected_sample;
            previous_valid <= 1'b1;

            if (!capture_triggered && accepted_count >= PRE_SAMPLES-1 &&
                trigger_hit) begin
              capture_triggered <= 1'b1;
              triggered <= 1'b1;
              post_count <= 1;
              if (capture_bank)
                trigger_index1 <= sample_index;
              else
                trigger_index0 <= sample_index;
            end else if (capture_triggered && trigger_mode != 2'd0) begin
              post_count <= post_count + 1'b1;
            end

            if ((trigger_mode == 2'd0 &&
                 accepted_count == SAMPLES_PER_FRAME-1) ||
                (trigger_mode != 2'd0 && capture_triggered &&
                 post_count == POST_SAMPLES-1)) begin
              capture_active <= 1'b0;
              if (capture_bank) begin
                bank_ready1 <= 1'b1;
                bank_start1 <= write_ptr + 1'b1;
                first_index1 <= sample_index -
                    ((SAMPLES_PER_FRAME-1) << decim_value);
                frame_seq1 <= frame_count;
                frame_cfg1 <= {12'd0, fps_20, trigger_channel,
                    trigger_mode, 8'd0, decim_value};
              end else begin
                bank_ready0 <= 1'b1;
                bank_start0 <= write_ptr + 1'b1;
                first_index0 <= sample_index -
                    ((SAMPLES_PER_FRAME-1) << decim_value);
                frame_seq0 <= frame_count;
                frame_cfg0 <= {12'd0, fps_20, trigger_channel,
                    trigger_mode, 8'd0, decim_value};
              end
              frame_count <= frame_count + 1'b1;
              capture_bank <= ~capture_bank;
            end
          end else begin
            decim_count <= decim_count + 1'b1;
          end
        end
      end

      if (!send_active && (bank_ready0 || bank_ready1)) begin
        send_active <= 1'b1;
        send_state <= SEND_LOAD;
        send_word <= 0;
        scope_valid <= 1'b0;
        scope_last <= 1'b0;
        if (bank_ready0) begin
          send_bank <= 1'b0;
          send_start <= bank_start0;
          send_first_index <= first_index0;
          send_trigger_index <= trigger_index0;
          send_frame_seq <= frame_seq0;
          send_cfg <= frame_cfg0;
          send_otr <= frame_otr0;
        end else begin
          send_bank <= 1'b1;
          send_start <= bank_start1;
          send_first_index <= first_index1;
          send_trigger_index <= trigger_index1;
          send_frame_seq <= frame_seq1;
          send_cfg <= frame_cfg1;
          send_otr <= frame_otr1;
        end
      end else if (send_active) begin
        case (send_state)
          SEND_LOAD: begin
            scope_valid <= 1'b0;
            scope_last <= 1'b0;
            if (send_word < HEADER_WORDS) begin
              scope_data <= header_word(send_word[3:0]);
              scope_last <= (send_word == TOTAL_WORDS-1);
              scope_valid <= 1'b1;
              send_state <= SEND_AXIS;
            end else begin
              ram_read_addr <= send_start + (send_word - HEADER_WORDS);
              send_state <= SEND_RAM_WAIT;
            end
          end

          SEND_RAM_WAIT: begin
            // One complete cycle is required after changing ram_read_addr:
            // the BRAM output register is updated at this clock edge.
            send_state <= SEND_RAM_DATA;
          end

          SEND_RAM_DATA: begin
            scope_data <= send_bank ? bank1_q : bank0_q;
            scope_last <= (send_word == TOTAL_WORDS-1);
            scope_valid <= 1'b1;
            send_state <= SEND_AXIS;
          end

          default: begin
            if (scope_valid && scope_ready) begin
              scope_valid <= 1'b0;
              scope_last <= 1'b0;
              if (send_word == TOTAL_WORDS-1) begin
                send_active <= 1'b0;
                if (send_bank)
                  bank_ready1 <= 1'b0;
                else
                  bank_ready0 <= 1'b0;
              end else begin
                send_word <= send_word + 1'b1;
                send_state <= SEND_LOAD;
              end
            end
          end
        endcase
      end else begin
        scope_valid <= 1'b0;
        scope_last <= 1'b0;
      end
    end
  end
endmodule
