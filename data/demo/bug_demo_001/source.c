struct demo_dev {
    int queue;
};

struct demo_ctx {
    struct demo_dev *dev;
};

static int demo_send_packet(struct demo_ctx *ctx)
{
    int q = ctx->dev->queue;

    if (q < 0)
        return -1;

    return q;
}

static int demo_ioctl(struct demo_ctx *ctx)
{
    return demo_send_packet(ctx);
}

