/*
 * Source excerpt reconstructed from developer patch context.
 * Replace with the full localization file when a Linux checkout is available.
 */


/* diff --git a/drivers/usb/usbip/vhci_hcd.c b/drivers/usb/usbip/vhci_hcd.c */

/* @@ -396,6 +396,8 @@ static int vhci_hub_control(struct usb_hcd *hcd, u16 typeReq, u16 wValue, */
		default:
			usbip_dbg_vhci_rh(" ClearPortFeature: default %x\n",
					  wValue);
			vhci_hcd->port_status[rhport] &= ~(1 << wValue);
			break;
		}
