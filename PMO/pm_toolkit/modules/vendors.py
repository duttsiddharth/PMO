"""Vendor & Procurement Management: vendor master, POs, SLA, delivery & invoice tracking."""
import pandas as pd
import streamlit as st

from core import models as m
from modules.common import project_picker, get_session, section_title


def render():
    section_title("Vendor & Procurement", "Vendor master, purchase orders, SLA and delivery tracking")
    s = get_session()

    tab_v, tab_po = st.tabs(["Vendor Master & SLA", "Purchase Orders"])

    with tab_v:
        vendors = s.query(m.Vendor).all()
        vdf = pd.DataFrame([{ "Vendor": v.name, "Category": v.category, "Contact": v.contact,
                              "SLA Target": v.sla_target, "SLA Status": v.sla_status} for v in vendors])
        st.dataframe(vdf, use_container_width=True, hide_index=True)
        with st.expander("Add vendor"):
            with st.form("add_vendor"):
                c = st.columns(2)
                name = c[0].text_input("Vendor name")
                cat = c[1].text_input("Category")
                contact = c[0].text_input("Contact")
                sla = c[1].text_input("SLA target")
                status = st.selectbox("SLA status", ["On Track", "At Risk", "Breached"])
                if st.form_submit_button("Add") and name:
                    s.add(m.Vendor(name=name, category=cat, contact=contact,
                                   sla_target=sla, sla_status=status))
                    s.commit(); st.rerun()

    with tab_po:
        p = project_picker(key="po_proj")
        pos = s.query(m.PurchaseOrder).filter_by(project_id=p.id).all()
        vendor_name = {v.id: v.name for v in s.query(m.Vendor).all()}
        pdf = pd.DataFrame([{ "PO #": po.po_number, "Vendor": vendor_name.get(po.vendor_id, "-"),
                              "Description": po.description, "Amount": po.amount,
                              "Status": po.status, "Delivery": po.delivery_status,
                              "Invoice": po.invoice_status} for po in pos])
        if not pdf.empty:
            k = st.columns(3)
            k[0].metric("Total POs", len(pdf))
            k[1].metric("PO value", f"{pdf['Amount'].sum():,.0f}")
            k[2].metric("Delivered", int((pdf["Delivery"] == "Delivered").sum()))
        st.dataframe(pdf, use_container_width=True, hide_index=True)
