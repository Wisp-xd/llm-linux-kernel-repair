/*
 * Source excerpt reconstructed from developer patch context.
 * Replace with the full localization file when a Linux checkout is available.
 */


/* diff --git a/mm/filemap.c b/mm/filemap.c */

/* @@ -3378,7 +3378,7 @@ vm_fault_t filemap_fault(struct vm_fault *vmf) */
	 * re-find the vma and come back and find our hopefully still populated
	 * page.
	 */
	if (folio)
		folio_put(folio);
	if (mapping_locked)
		filemap_invalidate_unlock_shared(mapping);
