`timescale 1ns / 1ps

// AD9269 3-wire SPI configuration with mandatory write-back verification.
// For reads SDIO is released after the 16-bit instruction and sampled during
// the final eight rising SCLK edges.  Three complete attempts are permitted.
module ad9269_spi_init #(
    parameter integer STARTUP_CYCLES = 5000000,
    parameter integer HALF_PERIOD_CYCLES = 5
)(
    input  wire       clk,
    input  wire       resetn,
    input  wire       reinit_toggle,
    input  wire [2:0] test_mode,
    input  wire       sdio_i,
    input  wire       acquisition_stopped,
    output reg        csb,
    output reg        sclk,
    output reg        sdio_o,
    output reg        sdio_oe,
    output reg        busy,
    output reg        done,
    output reg        error,
    output reg [7:0]  chip_id,
    output reg [7:0]  chip_grade,
    output reg [7:0]  readback_14,
    output reg [7:0]  readback_17,
    output reg [7:0]  readback_0d,
    output reg [31:0] error_detail
);
  localparam ST_WAIT=0, ST_LOAD=1, ST_SHIFT=2, ST_GAP=3,
             ST_VERIFY=4, ST_DONE=5, ST_FAILED=6;
  reg [2:0] state;
  reg [31:0] delay_count, divider_count;
  reg [23:0] shift_reg;
  reg [5:0] edge_count;
  reg [3:0] command_index;
  reg [1:0] attempt;
  reg [7:0] read_value;
  reg reinit_seen;
  (* ASYNC_REG = "TRUE" *) reg reinit_s1, reinit_s2;
  (* ASYNC_REG = "TRUE" *) reg [2:0] mode_s1, mode_s2;
  wire reinit_request = reinit_s2 ^ reinit_seen;
  wire is_read = command_index >= 4;
  wire [23:0] next_command = command_word(command_index, mode_s2);

  function [23:0] command_word;
    input [3:0] index;
    input [2:0] requested_mode;
    begin
      case (index)
        0: command_word = {8'h00,8'h14,8'h21};
        1: command_word = {8'h00,8'h17,8'h27};
        2: command_word = {8'h00,8'h0d,5'd0,requested_mode};
        3: command_word = {8'h00,8'hff,8'h01};
        4: command_word = {8'h80,8'h01,8'h00};
        5: command_word = {8'h80,8'h02,8'h00};
        6: command_word = {8'h80,8'h14,8'h00};
        7: command_word = {8'h80,8'h17,8'h00};
        8: command_word = {8'h80,8'h0d,8'h00};
        default: command_word = 24'd0;
      endcase
    end
  endfunction

  always @(posedge clk) begin
    if (!resetn) begin
      state<=ST_WAIT; delay_count<=0; divider_count<=0; shift_reg<=0;
      edge_count<=0; command_index<=0; attempt<=0; read_value<=0;
      reinit_seen<=0; reinit_s1<=0; reinit_s2<=0; mode_s1<=0; mode_s2<=0;
      csb<=1; sclk<=1; sdio_o<=0; sdio_oe<=0;
      busy<=1; done<=0; error<=0; chip_id<=0; chip_grade<=0;
      readback_14<=0; readback_17<=0; readback_0d<=0; error_detail<=0;
    end else begin
      reinit_s1 <= reinit_toggle;
      reinit_s2 <= reinit_s1;
      mode_s1 <= test_mode;
      mode_s2 <= mode_s1;
      case (state)
        ST_WAIT: begin
          csb<=1; sclk<=1; sdio_oe<=0; busy<=1; done<=0; error<=0;
          if (delay_count >= STARTUP_CYCLES-1 && acquisition_stopped) begin
            delay_count<=0; command_index<=0; attempt<=0; state<=ST_LOAD;
          end else if (delay_count < STARTUP_CYCLES-1)
            delay_count<=delay_count+1'b1;
        end
        ST_LOAD: begin
          if (!acquisition_stopped) begin
            csb<=1; sclk<=1; sdio_oe<=0; state<=ST_FAILED;
            error<=1; error_detail<=32'h04000001;
          end else begin
            shift_reg<=next_command;
            sdio_o<=next_command[23];
            sdio_oe<=1; read_value<=0; edge_count<=0; divider_count<=0;
            csb<=0; sclk<=0; state<=ST_SHIFT;
          end
        end
        ST_SHIFT: begin
          if (divider_count >= HALF_PERIOD_CYCLES-1) begin
            divider_count<=0;
            if (!sclk) begin
              sclk<=1;
              if (is_read && edge_count>=16)
                read_value <= {read_value[6:0],sdio_i};
              if (edge_count==23)
                state<=ST_GAP;
              else
                edge_count<=edge_count+1'b1;
            end else begin
              sclk<=0;
              shift_reg<={shift_reg[22:0],1'b0};
              sdio_o<=shift_reg[22];
              // Release the 3-wire bus only after all 16 instruction bits
              // (edge_count 0..15) have been clocked on rising edges.
              if (is_read && edge_count>=16)
                sdio_oe<=0;
            end
          end else divider_count<=divider_count+1'b1;
        end
        ST_GAP: begin
          csb<=1; sclk<=1; sdio_oe<=0; divider_count<=0;
          case (command_index)
            4: chip_id<=read_value;
            5: chip_grade<=read_value;
            6: readback_14<=read_value;
            7: readback_17<=read_value;
            8: readback_0d<=read_value;
          endcase
          if (command_index==8) state<=ST_VERIFY;
          else begin command_index<=command_index+1'b1; state<=ST_LOAD; end
        end
        ST_VERIFY: begin
          if (chip_id==8'h75 && readback_14==8'h21 &&
              readback_17==8'h27 && readback_0d=={5'd0,mode_s2}) begin
            busy<=0; done<=1; error<=0; error_detail<=0;
            reinit_seen<=reinit_s2; state<=ST_DONE;
          end else if (attempt<2) begin
            attempt<=attempt+1'b1; command_index<=0; state<=ST_LOAD;
          end else begin
            busy<=0; done<=0; error<=1;
            error_detail<={attempt,6'd0,chip_id,readback_14,
                (readback_17 ^ {5'd0,mode_s2})};
            reinit_seen<=reinit_s2; state<=ST_FAILED;
          end
        end
        ST_DONE: begin
          csb<=1; sclk<=1; sdio_oe<=0; busy<=0; done<=1;
          if (reinit_request && acquisition_stopped) begin
            reinit_seen<=reinit_s2; command_index<=0; attempt<=0;
            done<=0; busy<=1; state<=ST_LOAD;
          end
        end
        ST_FAILED: begin
          csb<=1; sclk<=1; sdio_oe<=0; busy<=0;
          if (reinit_request && acquisition_stopped) begin
            reinit_seen<=reinit_s2; command_index<=0; attempt<=0;
            error<=0; error_detail<=0; busy<=1; state<=ST_LOAD;
          end
        end
        default: state<=ST_WAIT;
      endcase
    end
  end
endmodule
