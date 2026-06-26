/*
 * Source excerpt reconstructed from developer patch context.
 * Replace with the full localization file when a Linux checkout is available.
 */


/* diff --git a/kernel/printk/printk.c b/kernel/printk/printk.c */

/* @@ -1399,7 +1399,7 @@ static size_t record_print_text(struct printk_record *r, bool syslog, */
	 * not counted in the return value.
	 */
	if (buf_size > 0)
		text[len] = 0;

	return len;
}
