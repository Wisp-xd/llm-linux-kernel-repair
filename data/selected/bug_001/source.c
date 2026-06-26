/*
 * Source excerpt reconstructed from developer patch context.
 * Replace with the full localization file when a Linux checkout is available.
 */


/* diff --git a/net/netfilter/nf_tables_api.c b/net/netfilter/nf_tables_api.c */

/* @@ -2166,8 +2166,10 @@ static int nft_basechain_init(struct nft_base_chain *basechain, u8 family, */
	chain->flags |= NFT_CHAIN_BASE | flags;
	basechain->policy = NF_ACCEPT;
	if (chain->flags & NFT_CHAIN_HW_OFFLOAD &&
	    !nft_chain_offload_support(basechain))
		return -EOPNOTSUPP;

	flow_block_init(&basechain->flow_block);
