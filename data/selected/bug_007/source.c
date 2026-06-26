/*
 * Source excerpt reconstructed from developer patch context.
 * Replace with the full localization file when a Linux checkout is available.
 */


/* diff --git a/drivers/media/common/videobuf2/videobuf2-core.c b/drivers/media/common/videobuf2/videobuf2-core.c */

/* @@ -812,6 +812,9 @@ int vb2_core_create_bufs(struct vb2_queue *q, enum vb2_memory memory, */
		memset(q->alloc_devs, 0, sizeof(q->alloc_devs));
		q->memory = memory;
		q->waiting_for_buffers = !q->is_output;
	}

	num_buffers = min(*count, VB2_MAX_FRAME - q->num_buffers);
