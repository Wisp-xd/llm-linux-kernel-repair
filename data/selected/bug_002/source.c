/*
 * Source excerpt reconstructed from developer patch context.
 * Replace with the full localization file when a Linux checkout is available.
 */


/* diff --git a/drivers/media/usb/dvb-usb/cinergyT2-core.c b/drivers/media/usb/dvb-usb/cinergyT2-core.c */

/* @@ -78,6 +78,8 @@ static int cinergyt2_frontend_attach(struct dvb_usb_adapter *adap) */

	ret = dvb_usb_generic_rw(d, st->data, 1, st->data, 3, 0);
	if (ret < 0) {
		deb_rc("cinergyt2_power_ctrl() Failed to retrieve sleep state info\n");
	}
	mutex_unlock(&d->data_mutex);
