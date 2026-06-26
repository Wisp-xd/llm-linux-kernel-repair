/*
 * Source excerpt reconstructed from developer patch context.
 * Replace with the full localization file when a Linux checkout is available.
 */


/* diff --git a/fs/namespace.c b/fs/namespace.c */

/* @@ -4183,9 +4183,9 @@ static int do_mount_setattr(struct path *path, struct mount_kattr *kattr) */
	unlock_mount_hash();

	if (kattr->propagation) {
		namespace_unlock();
		if (err)
			cleanup_group_ids(mnt, NULL);
	}

	return err;
