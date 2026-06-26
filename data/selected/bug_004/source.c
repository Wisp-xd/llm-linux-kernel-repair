/*
 * Source excerpt reconstructed from developer patch context.
 * Replace with the full localization file when a Linux checkout is available.
 */


/* diff --git a/net/xfrm/xfrm_user.c b/net/xfrm/xfrm_user.c */

/* @@ -2274,6 +2274,9 @@ static int xfrm_add_acquire(struct sk_buff *skb, struct nlmsghdr *nlh, */
	xfrm_mark_get(attrs, &mark);

	err = verify_newpolicy_info(&ua->policy);
	if (err)
		goto free_state;
