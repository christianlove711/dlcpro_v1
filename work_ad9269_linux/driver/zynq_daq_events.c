// SPDX-License-Identifier: GPL-2.0
/*
 * AD9269 final dual-DMA client.
 *
 * Event DMA: 64 x 8,320-byte frames, AXI DMA 0 / HP0.
 * Scope DMA: 16 x 32,832-byte frames, AXI DMA 1 / HP1.
 *
 * Both DMAengine channels and coherent rings are independent.  Acquisition
 * mode is mutually exclusive in PL, so a single character device exposes the
 * active ring without ever reconfiguring one DMA channel for the other format.
 */
#include <linux/atomic.h>
#include <linux/bitmap.h>
#include <linux/cdev.h>
#include <linux/dma-mapping.h>
#include <linux/dmaengine.h>
#include <linux/fs.h>
#include <linux/io.h>
#include <linux/module.h>
#include <linux/mutex.h>
#include <linux/of_dma.h>
#include <linux/platform_device.h>
#include <linux/poll.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include "../include/zynq_daq.h"

#define MAX_RING_SLOTS              ZYNQ_DAQ_RING_SLOTS

#define DAQ_REG_CONTROL             0x08
#define DAQ_REG_STATUS              0x0c
#define DAQ_REG_FIFO_LEVEL          0x14
#define DAQ_REG_ADC_CONFIG          0x38
#define DAQ_REG_STREAM_ID           0x54
#define DAQ_REG_MEASURED_RATE       0x58
#define DAQ_REG_EVENT_COUNT         0x5c
#define DAQ_REG_DROPPED_EVENTS      0x60
#define DAQ_REG_LAST_ERROR          0x64
#define DAQ_REG_EVENT_CONTROL       0x68
#define DAQ_REG_SUPPRESSED_EVENTS   0x6c
#define DAQ_REG_ACQ_MODE            0x70
#define DAQ_REG_SCOPE_CONTROL       0x74
#define DAQ_REG_SCOPE_CONFIG        0x78
#define DAQ_REG_SCOPE_STATUS        0x7c
#define DAQ_REG_SCOPE_FRAME_COUNT   0x80
#define DAQ_REG_SPI_ID_GRADE        0x84
#define DAQ_REG_SPI_ERROR_DETAIL    0x90
#define DAQ_REG_EVENT_DMA_STATUS    0x94
#define DAQ_REG_SCOPE_SUPPRESSED    0x98
#define DAQ_REG_SCOPE_DROPPED       0x9c

#define DAQ_CTL_START               BIT(0)
#define DAQ_CTL_STOP                BIT(1)
#define DAQ_CTL_CONFIG_COMMIT       BIT(2)
#define DAQ_EVENT_ENABLE            BIT(0)
#define DAQ_SCOPE_ARMED             BIT(0)
#define DAQ_SCOPE_ABORT             BIT(1)
#define DAQ_SCOPE_CLEAR             BIT(2)

#define DAQ_STATE_STOPPED           0U
#define DAQ_STATE_CONFIGURED        1U

struct daq_dev;
struct daq_ring;

struct daq_slot {
  struct daq_ring *ring;
  u32 index;
  u32 sequence;
  dma_cookie_t cookie;
};

struct daq_ring {
  struct daq_dev *owner;
  struct dma_chan *chan;
  const char *name;
  u32 mode;
  u32 slots;
  u32 frame_bytes;
  u32 stride;
  DECLARE_BITMAP(ready, MAX_RING_SLOTS);
  DECLARE_BITMAP(leased, MAX_RING_SLOTS);
  DECLARE_BITMAP(submitted, MAX_RING_SLOTS);
  void *cpu[MAX_RING_SLOTS];
  dma_addr_t dma[MAX_RING_SLOTS];
  struct daq_slot slot[MAX_RING_SLOTS];
  u32 sequence;
  u32 errors;
  bool running;
};

struct daq_dev {
  struct device *dev;
  void __iomem *regs;
  struct cdev cdev;
  dev_t devt;
  wait_queue_head_t wait;
  spinlock_t lock;
  struct mutex ioctl_lock;
  atomic_t opened;
  struct daq_ring event;
  struct daq_ring scope;
  struct daq_ring *active;
  u32 rate;
  u32 mode;
};

static struct class *daq_class;

static int daq_rate_to_sel(u32 rate_hz, u32 *selector)
{
  switch (rate_hz) {
  case 5000000:  *selector = 1; return 0;
  case 10000000: *selector = 2; return 0;
  case 20000000: *selector = 3; return 0;
  case 40000000: *selector = 4; return 0;
  case 80000000: *selector = 5; return 0;
  default: return -EINVAL;
  }
}

static void daq_complete(void *arg)
{
  struct daq_slot *slot = arg;
  struct daq_ring *ring = slot->ring;
  struct daq_dev *d = ring->owner;
  unsigned long flags;

  spin_lock_irqsave(&d->lock, flags);
  __clear_bit(slot->index, ring->submitted);
  if (ring->running && !test_bit(slot->index, ring->leased)) {
    slot->sequence = ++ring->sequence;
    __set_bit(slot->index, ring->ready);
  }
  spin_unlock_irqrestore(&d->lock, flags);
  wake_up_interruptible(&d->wait);
}

static int daq_submit_slot(struct daq_ring *ring, u32 index)
{
  struct daq_dev *d = ring->owner;
  struct dma_async_tx_descriptor *tx;
  struct daq_slot *slot = &ring->slot[index];
  unsigned long flags;
  dma_cookie_t cookie;

  spin_lock_irqsave(&d->lock, flags);
  if (!ring->running || test_bit(index, ring->submitted)) {
    spin_unlock_irqrestore(&d->lock, flags);
    return 0;
  }
  __set_bit(index, ring->submitted);
  spin_unlock_irqrestore(&d->lock, flags);

  tx = dmaengine_prep_slave_single(ring->chan, ring->dma[index],
      ring->frame_bytes, DMA_DEV_TO_MEM,
      DMA_PREP_INTERRUPT | DMA_CTRL_ACK);
  if (!tx)
    goto submit_error;
  tx->callback = daq_complete;
  tx->callback_param = slot;
  cookie = dmaengine_submit(tx);
  if (dma_submit_error(cookie))
    goto submit_error;
  slot->cookie = cookie;
  return 0;

submit_error:
  spin_lock_irqsave(&d->lock, flags);
  __clear_bit(index, ring->submitted);
  ring->errors++;
  spin_unlock_irqrestore(&d->lock, flags);
  return -EIO;
}

static void daq_ring_reset_locked(struct daq_ring *ring)
{
  u32 i;

  ring->running = false;
  bitmap_zero(ring->ready, MAX_RING_SLOTS);
  bitmap_zero(ring->leased, MAX_RING_SLOTS);
  bitmap_zero(ring->submitted, MAX_RING_SLOTS);
  for (i = 0; i < ring->slots; i++)
    ring->slot[i].cookie = -EINVAL;
}

static void daq_stop_locked(struct daq_dev *d)
{
  unsigned long flags;

  /* Stop PL first, then remove both independent producer arm levels. */
  writel(DAQ_CTL_STOP, d->regs + DAQ_REG_CONTROL);
  writel(0, d->regs + DAQ_REG_EVENT_CONTROL);
  writel(DAQ_SCOPE_ABORT, d->regs + DAQ_REG_SCOPE_CONTROL);
  readl(d->regs + DAQ_REG_STATUS);

  if (d->event.chan)
    dmaengine_terminate_sync(d->event.chan);
  if (d->scope.chan)
    dmaengine_terminate_sync(d->scope.chan);

  spin_lock_irqsave(&d->lock, flags);
  daq_ring_reset_locked(&d->event);
  daq_ring_reset_locked(&d->scope);
  d->active = NULL;
  spin_unlock_irqrestore(&d->lock, flags);
  wake_up_interruptible(&d->wait);
}

static int daq_commit(struct daq_dev *d, u32 rate_hz, u32 mode)
{
  u32 adc_config, selector, state;
  int ret;

  if (mode != ZYNQ_DAQ_MODE_SCOPE && mode != ZYNQ_DAQ_MODE_EVENT)
    return -EINVAL;
  ret = daq_rate_to_sel(rate_hz, &selector);
  if (ret)
    return ret;
  state = readl(d->regs + DAQ_REG_STATUS) & 0x7;
  if (d->active || (state != DAQ_STATE_STOPPED &&
                    state != DAQ_STATE_CONFIGURED))
    return -EBUSY;

  adc_config = readl(d->regs + DAQ_REG_ADC_CONFIG);
  adc_config &= ~GENMASK(10, 8);
  adc_config |= BIT(16) | selector << 8; /* AD9269 is fixed. */
  writel(adc_config, d->regs + DAQ_REG_ADC_CONFIG);
  writel(mode, d->regs + DAQ_REG_ACQ_MODE);
  d->rate = rate_hz;
  d->mode = mode;
  return 0;
}

static int daq_start_ring(struct daq_dev *d, struct daq_ring *ring)
{
  unsigned long flags;
  u32 i;
  int ret;

  spin_lock_irqsave(&d->lock, flags);
  daq_ring_reset_locked(ring);
  ring->running = true;
  d->active = ring;
  spin_unlock_irqrestore(&d->lock, flags);

  for (i = 0; i < ring->slots; i++) {
    ret = daq_submit_slot(ring, i);
    if (ret)
      goto fail;
  }
  dma_async_issue_pending(ring->chan);

  /* Arm only after every descriptor has been submitted and issued. */
  if (ring->mode == ZYNQ_DAQ_MODE_EVENT) {
    writel(DAQ_EVENT_ENABLE, d->regs + DAQ_REG_EVENT_CONTROL);
    readl(d->regs + DAQ_REG_EVENT_CONTROL);
  } else {
    writel(DAQ_SCOPE_ARMED | DAQ_SCOPE_CLEAR,
           d->regs + DAQ_REG_SCOPE_CONTROL);
    readl(d->regs + DAQ_REG_SCOPE_CONTROL);
  }
  /* Commit the stopped-state configuration only after the complete receive
   * ring exists and the selected producer has been armed. */
  writel(DAQ_CTL_CONFIG_COMMIT, d->regs + DAQ_REG_CONTROL);
  readl(d->regs + DAQ_REG_STATUS);
  writel(DAQ_CTL_START, d->regs + DAQ_REG_CONTROL);
  readl(d->regs + DAQ_REG_STATUS);
  return 0;

fail:
  daq_stop_locked(d);
  return ret;
}

static int daq_start_event(struct daq_dev *d,
                           const struct zynq_daq_config *cfg)
{
  int ret;

  if (cfg->threshold)
    return -EOPNOTSUPP;
  ret = daq_commit(d, cfg->rate_hz, ZYNQ_DAQ_MODE_EVENT);
  return ret ? ret : daq_start_ring(d, &d->event);
}

static int daq_start_scope(struct daq_dev *d,
                           const struct zynq_scope_config *cfg)
{
  u32 scope_config;
  int ret;

  if (cfg->decimation_log2 > 8 ||
      cfg->trigger_mode > ZYNQ_SCOPE_TRIGGER_FALLING ||
      cfg->trigger_channel > 1 ||
      (cfg->fps != 10 && cfg->fps != 20) ||
      cfg->trigger_level < -32768 || cfg->trigger_level > 32767)
    return -EINVAL;

  ret = daq_commit(d, cfg->rate_hz, ZYNQ_DAQ_MODE_SCOPE);
  if (ret)
    return ret;
  scope_config = cfg->decimation_log2 |
      (cfg->trigger_mode << 4) |
      (cfg->trigger_channel << 6) |
      ((cfg->fps == 20) ? BIT(7) : 0) |
      ((u32)(u16)(s16)cfg->trigger_level << 16);
  writel(scope_config, d->regs + DAQ_REG_SCOPE_CONFIG);
  readl(d->regs + DAQ_REG_SCOPE_CONFIG);
  return daq_start_ring(d, &d->scope);
}

static bool daq_has_ready(struct daq_dev *d)
{
  struct daq_ring *ring = READ_ONCE(d->active);

  return ring && !bitmap_empty(ring->ready, ring->slots);
}

static long daq_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
  struct daq_dev *d = file->private_data;
  struct daq_ring *ring;
  struct zynq_daq_frame frame;
  struct zynq_daq_config cfg;
  struct zynq_scope_config scope_cfg;
  struct zynq_daq_status status;
  unsigned long flags;
  unsigned long index;
  u32 value;
  int ret = 0;

  switch (cmd) {
  case ZYNQ_DAQ_IOC_START:
    if (copy_from_user(&cfg, (void __user *)arg, sizeof(cfg)))
      return -EFAULT;
    mutex_lock(&d->ioctl_lock);
    ret = d->active ? -EBUSY : daq_start_event(d, &cfg);
    mutex_unlock(&d->ioctl_lock);
    return ret;

  case ZYNQ_DAQ_IOC_SCOPE_START:
    if (copy_from_user(&scope_cfg, (void __user *)arg, sizeof(scope_cfg)))
      return -EFAULT;
    mutex_lock(&d->ioctl_lock);
    ret = d->active ? -EBUSY : daq_start_scope(d, &scope_cfg);
    mutex_unlock(&d->ioctl_lock);
    return ret;

  case ZYNQ_DAQ_IOC_STOP:
    mutex_lock(&d->ioctl_lock);
    daq_stop_locked(d);
    mutex_unlock(&d->ioctl_lock);
    return 0;

  case ZYNQ_DAQ_IOC_SET_RATE:
    if (copy_from_user(&value, (void __user *)arg, sizeof(value)))
      return -EFAULT;
    mutex_lock(&d->ioctl_lock);
    ret = daq_commit(d, value, d->mode);
    mutex_unlock(&d->ioctl_lock);
    return ret;

  case ZYNQ_DAQ_IOC_SET_THRESH:
    return -EOPNOTSUPP;

  case ZYNQ_DAQ_IOC_DEQUEUE:
    ret = wait_event_interruptible(d->wait,
        daq_has_ready(d) || !READ_ONCE(d->active));
    if (ret)
      return ret;
    spin_lock_irqsave(&d->lock, flags);
    ring = d->active;
    if (!ring) {
      spin_unlock_irqrestore(&d->lock, flags);
      return -EPIPE;
    }
    index = find_first_bit(ring->ready, ring->slots);
    if (index >= ring->slots) {
      spin_unlock_irqrestore(&d->lock, flags);
      return -EAGAIN;
    }
    __clear_bit(index, ring->ready);
    __set_bit(index, ring->leased);
    memset(&frame, 0, sizeof(frame));
    frame.slot = index;
    frame.length = ring->frame_bytes;
    frame.sequence = ring->slot[index].sequence;
    frame.mode = ring->mode;
    frame.stride = ring->stride;
    frame.dma_addr = ring->dma[index];
    spin_unlock_irqrestore(&d->lock, flags);
    if (copy_to_user((void __user *)arg, &frame, sizeof(frame))) {
      spin_lock_irqsave(&d->lock, flags);
      __clear_bit(index, ring->leased);
      __set_bit(index, ring->ready);
      spin_unlock_irqrestore(&d->lock, flags);
      return -EFAULT;
    }
    return 0;

  case ZYNQ_DAQ_IOC_RELEASE:
    if (copy_from_user(&value, (void __user *)arg, sizeof(value)))
      return -EFAULT;
    mutex_lock(&d->ioctl_lock);
    ring = d->active;
    if (!ring || value >= ring->slots) {
      ret = -EINVAL;
      goto release_unlock;
    }
    spin_lock_irqsave(&d->lock, flags);
    if (!test_bit(value, ring->leased)) {
      spin_unlock_irqrestore(&d->lock, flags);
      ret = -EINVAL;
      goto release_unlock;
    }
    __clear_bit(value, ring->leased);
    spin_unlock_irqrestore(&d->lock, flags);
    ret = ring->running ? daq_submit_slot(ring, value) : -EPIPE;
    if (!ret)
      dma_async_issue_pending(ring->chan);
release_unlock:
    mutex_unlock(&d->ioctl_lock);
    return ret;

  case ZYNQ_DAQ_IOC_GET_STATUS:
    memset(&status, 0, sizeof(status));
    status.running = !!READ_ONCE(d->active);
    status.mode = READ_ONCE(d->mode);
    status.fifo_level = readl(d->regs + DAQ_REG_FIFO_LEVEL) & 0x7fff;
    status.dma_errors = READ_ONCE(d->event.errors) +
                        READ_ONCE(d->scope.errors);
    status.event_count = readl(d->regs + DAQ_REG_EVENT_COUNT);
    status.dropped_events = readl(d->regs + DAQ_REG_DROPPED_EVENTS);
    status.suppressed_events =
        readl(d->regs + DAQ_REG_SUPPRESSED_EVENTS);
    status.event_path_enabled =
        !!(readl(d->regs + DAQ_REG_EVENT_DMA_STATUS) & BIT(0));
    status.stream_id = readl(d->regs + DAQ_REG_STREAM_ID);
    status.measured_rate_hz = readl(d->regs + DAQ_REG_MEASURED_RATE);
    status.last_error = readl(d->regs + DAQ_REG_LAST_ERROR) & 0xff;
    status.scope_status = readl(d->regs + DAQ_REG_SCOPE_STATUS);
    status.scope_frame_count =
        readl(d->regs + DAQ_REG_SCOPE_FRAME_COUNT);
    status.scope_suppressed =
        readl(d->regs + DAQ_REG_SCOPE_SUPPRESSED);
    status.scope_dropped = readl(d->regs + DAQ_REG_SCOPE_DROPPED);
    status.spi_id_grade = readl(d->regs + DAQ_REG_SPI_ID_GRADE);
    status.spi_error_detail =
        readl(d->regs + DAQ_REG_SPI_ERROR_DETAIL);
    return copy_to_user((void __user *)arg, &status, sizeof(status)) ?
        -EFAULT : 0;

  case ZYNQ_DAQ_IOC_GET_MODE:
    value = READ_ONCE(d->mode);
    return copy_to_user((void __user *)arg, &value, sizeof(value)) ?
        -EFAULT : 0;

  default:
    return -ENOTTY;
  }
}

static int daq_mmap(struct file *file, struct vm_area_struct *vma)
{
  struct daq_dev *d = file->private_data;
  struct daq_ring *ring;
  unsigned long byte_offset = vma->vm_pgoff << PAGE_SHIFT;
  unsigned long length = vma->vm_end - vma->vm_start;
  u32 index;
  int ret;

  mutex_lock(&d->ioctl_lock);
  ring = d->active;
  if (!ring || length != ring->stride || byte_offset % ring->stride) {
    mutex_unlock(&d->ioctl_lock);
    return -EINVAL;
  }
  index = byte_offset / ring->stride;
  if (index >= ring->slots) {
    mutex_unlock(&d->ioctl_lock);
    return -EINVAL;
  }
  vma->vm_pgoff = 0;
  ret = dma_mmap_coherent(d->dev, vma, ring->cpu[index],
                          ring->dma[index], ring->stride);
  mutex_unlock(&d->ioctl_lock);
  return ret;
}

static __poll_t daq_poll(struct file *file, poll_table *wait)
{
  struct daq_dev *d = file->private_data;
  struct daq_ring *ring;
  __poll_t mask = 0;

  poll_wait(file, &d->wait, wait);
  ring = READ_ONCE(d->active);
  if (ring && !bitmap_empty(ring->ready, ring->slots))
    mask |= EPOLLIN | EPOLLRDNORM;
  if (!ring)
    mask |= EPOLLHUP;
  return mask;
}

static int daq_open(struct inode *inode, struct file *file)
{
  struct daq_dev *d = container_of(inode->i_cdev, struct daq_dev, cdev);

  if (atomic_cmpxchg(&d->opened, 0, 1))
    return -EBUSY;
  file->private_data = d;
  return 0;
}

static int daq_release_file(struct inode *inode, struct file *file)
{
  struct daq_dev *d = file->private_data;

  mutex_lock(&d->ioctl_lock);
  daq_stop_locked(d);
  mutex_unlock(&d->ioctl_lock);
  atomic_set(&d->opened, 0);
  return 0;
}

static const struct file_operations daq_fops = {
  .owner = THIS_MODULE,
  .open = daq_open,
  .release = daq_release_file,
  .unlocked_ioctl = daq_ioctl,
  .mmap = daq_mmap,
  .poll = daq_poll,
  .llseek = no_llseek,
};

static int daq_ring_init(struct daq_dev *d, struct daq_ring *ring,
                         const char *dma_name, u32 mode, u32 slots,
                         u32 frame_bytes, u32 stride)
{
  u32 i;

  ring->owner = d;
  ring->name = dma_name;
  ring->mode = mode;
  ring->slots = slots;
  ring->frame_bytes = frame_bytes;
  ring->stride = stride;
  ring->chan = dma_request_chan(d->dev, dma_name);
  if (IS_ERR(ring->chan))
    return PTR_ERR(ring->chan);

  for (i = 0; i < slots; i++) {
    ring->cpu[i] = dmam_alloc_coherent(d->dev, stride, &ring->dma[i],
                                        GFP_KERNEL);
    if (!ring->cpu[i]) {
      dma_release_channel(ring->chan);
      ring->chan = NULL;
      return -ENOMEM;
    }
    ring->slot[i].ring = ring;
    ring->slot[i].index = i;
    ring->slot[i].cookie = -EINVAL;
  }
  return 0;
}

static int daq_probe(struct platform_device *pdev)
{
  struct daq_dev *d;
  struct resource *resource;
  int ret;

  d = devm_kzalloc(&pdev->dev, sizeof(*d), GFP_KERNEL);
  if (!d)
    return -ENOMEM;
  d->dev = &pdev->dev;
  spin_lock_init(&d->lock);
  mutex_init(&d->ioctl_lock);
  atomic_set(&d->opened, 0);
  init_waitqueue_head(&d->wait);
  d->mode = ZYNQ_DAQ_MODE_EVENT;

  resource = platform_get_resource(pdev, IORESOURCE_MEM, 0);
  if (!resource)
    return -ENODEV;
  d->regs = devm_ioremap_resource(&pdev->dev, resource);
  if (IS_ERR(d->regs))
    return PTR_ERR(d->regs);

  ret = daq_ring_init(d, &d->event, "event-rx",
      ZYNQ_DAQ_MODE_EVENT, ZYNQ_DAQ_RING_SLOTS,
      ZYNQ_DAQ_FRAME_BYTES, ZYNQ_DAQ_SLOT_BYTES);
  if (ret)
    return ret;
  ret = daq_ring_init(d, &d->scope, "scope-rx",
      ZYNQ_DAQ_MODE_SCOPE, ZYNQ_SCOPE_RING_SLOTS,
      ZYNQ_SCOPE_FRAME_BYTES, ZYNQ_SCOPE_SLOT_BYTES);
  if (ret)
    goto release_event;

  ret = alloc_chrdev_region(&d->devt, 0, 1, "zynq_daq");
  if (ret)
    goto release_scope;
  cdev_init(&d->cdev, &daq_fops);
  ret = cdev_add(&d->cdev, d->devt, 1);
  if (ret)
    goto unregister_chrdev;
  if (IS_ERR(device_create(daq_class, &pdev->dev, d->devt, d,
                           "zynq_daq"))) {
    ret = -ENODEV;
    goto delete_cdev;
  }
  platform_set_drvdata(pdev, d);
  return 0;

delete_cdev:
  cdev_del(&d->cdev);
unregister_chrdev:
  unregister_chrdev_region(d->devt, 1);
release_scope:
  dma_release_channel(d->scope.chan);
release_event:
  dma_release_channel(d->event.chan);
  return ret;
}

static int daq_remove(struct platform_device *pdev)
{
  struct daq_dev *d = platform_get_drvdata(pdev);

  mutex_lock(&d->ioctl_lock);
  daq_stop_locked(d);
  mutex_unlock(&d->ioctl_lock);
  device_destroy(daq_class, d->devt);
  cdev_del(&d->cdev);
  unregister_chrdev_region(d->devt, 1);
  dma_release_channel(d->scope.chan);
  dma_release_channel(d->event.chan);
  return 0;
}

static const struct of_device_id daq_of_match[] = {
  { .compatible = "acme,zynq-daq-dualdma-2.0" },
  {}
};
MODULE_DEVICE_TABLE(of, daq_of_match);

static struct platform_driver daq_driver = {
  .probe = daq_probe,
  .remove = daq_remove,
  .driver = {
    .name = "zynq_daq",
    .of_match_table = daq_of_match,
  },
};

static int __init daq_init(void)
{
  int ret;

  daq_class = class_create(THIS_MODULE, "zynq_daq");
  if (IS_ERR(daq_class))
    return PTR_ERR(daq_class);
  ret = platform_driver_register(&daq_driver);
  if (ret)
    class_destroy(daq_class);
  return ret;
}

static void __exit daq_exit(void)
{
  platform_driver_unregister(&daq_driver);
  class_destroy(daq_class);
}

module_init(daq_init);
module_exit(daq_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("AD9269 independent Event/Scope SG DMAengine client");
