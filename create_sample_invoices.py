"""
create_sample_invoices.py - Utility to generate realistic Indian GST test invoices
Updated for Phase 9: Includes duplicate invoice to test duplicate detection engine.
"""

from pathlib import Path
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image, ImageDraw
import config


def create_invoice_1(output_path: Path):
    """Format A: Intra-State B2B Tax Invoice (CGST + SGST)."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'InvoiceTitle', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=15, textColor=colors.HexColor("#1A365D")
    )
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Spacer(1, 10))

    info_data = [
        [
            Paragraph("<b>SUPPLIER DETAILS:</b><br/>"
                      "Apex Tech Solutions Pvt Ltd<br/>"
                      "Plot No. 45, MIDC Industrial Area, Andheri East<br/>"
                      "Mumbai, Maharashtra - 400093<br/>"
                      "<b>GSTIN:</b> 27AAACA1234A1Z5<br/>"
                      "<b>State:</b> Maharashtra (Code: 27)", styles['Normal']),
            Paragraph("<b>INVOICE DETAILS:</b><br/>"
                      "<b>Invoice No:</b> AT-2026-0891<br/>"
                      "<b>Invoice Date:</b> 15/10/2026<br/>"
                      "<b>PO Number:</b> PO-99412<br/>"
                      "<b>Place of Supply:</b> 27-Maharashtra<br/>"
                      "<b>Reverse Charge:</b> No", styles['Normal'])
        ]
    ]
    info_table = Table(info_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    item_data = [
        ["Sr.", "Description of Goods / Services", "HSN/SAC", "Qty", "Rate (Rs.)", "Taxable Value (Rs.)"],
        ["1", "IT Support & Cloud Hosting Services", "998315", "1 Month", "50,000.00", "50,000.00"],
    ]
    item_table = Table(item_data, colWidths=[30, 220, 70, 60, 80, 80])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 10))

    tax_data = [
        ["", "Taxable Value:", "50,000.00"],
        ["", "CGST @ 9%:", "4,500.00"],
        ["", "SGST @ 9%:", "4,500.00"],
        ["", "IGST @ 0%:", "0.00"],
        ["", "Cess:", "0.00"],
        ["", "Total Tax:", "9,000.00"],
        ["", "Invoice Total (INR):", "59,000.00"]
    ]
    tax_table = Table(tax_data, colWidths=[280, 160, 100])
    tax_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (1,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (1,-1), (-1,-1), 11),
        ('LINEABOVE', (1,-1), (-1,-1), 1, colors.HexColor("#2B6CB0")),
        ('LINEBELOW', (1,-1), (-1,-1), 1, colors.HexColor("#2B6CB0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tax_table)
    doc.build(story)


def create_invoice_2(output_path: Path):
    """Format A2: Inter-State B2B Tax Invoice (IGST)."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'InvoiceTitle', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=15, textColor=colors.HexColor("#2C5282")
    )
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Spacer(1, 10))

    info_data = [
        [
            Paragraph("<b>SUPPLIER DETAILS:</b><br/>"
                      "Bharat Electricals & Hardware Ltd<br/>"
                      "12, Industrial Estate, Peenya 2nd Phase<br/>"
                      "Bengaluru, Karnataka - 560058<br/>"
                      "<b>GSTIN:</b> 29AAACB4567B1Z8<br/>"
                      "<b>State:</b> Karnataka (Code: 29)", styles['Normal']),
            Paragraph("<b>INVOICE DETAILS:</b><br/>"
                      "<b>Invoice Number:</b> BE-INV/26/1042<br/>"
                      "<b>Date:</b> 22-10-2026<br/>"
                      "<b>PO No:</b> PO-2026-781<br/>"
                      "<b>Place of Supply:</b> 27-Maharashtra<br/>"
                      "<b>Reverse Charge (RCM):</b> No", styles['Normal'])
        ]
    ]
    info_table = Table(info_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    item_data = [
        ["S.N.", "Item Description", "HSN Code", "Qty", "Unit Price", "Total Amount (Rs.)"],
        ["1", "Industrial Transformers 500kVA", "850422", "1 Nos", "1,00,000.00", "1,00,000.00"],
    ]
    item_table = Table(item_data, colWidths=[30, 220, 70, 60, 80, 80])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('ALIGN', (4,1), (-1,-1), 'RIGHT'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 10))

    tax_data = [
        ["", "Taxable Value:", "1,00,000.00"],
        ["", "IGST @ 18%:", "18,000.00"],
        ["", "CGST:", "0.00"],
        ["", "SGST:", "0.00"],
        ["", "Total Tax Amount:", "18,000.00"],
        ["", "Invoice Total:", "1,18,000.00"]
    ]
    tax_table = Table(tax_data, colWidths=[280, 160, 100])
    tax_table.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (1,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (1,-1), (-1,-1), 11),
        ('LINEABOVE', (1,-1), (-1,-1), 1, colors.HexColor("#2B6CB0")),
        ('LINEBELOW', (1,-1), (-1,-1), 1, colors.HexColor("#2B6CB0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(tax_table)
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Terms:</b> Payment due within 30 days of invoice date.", styles['Italic']))
    doc.build(story)


def create_invoice_4_retail(output_path: Path):
    """Format B: Retail Style."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>COMMERCIAL TAX INVOICE</b>", styles['Title']))
    story.append(Spacer(1, 10))

    header_text = (
        "<b>Sold By:</b> Reliance Retail Limited<br/>"
        "3rd Floor, Court House, Lokmanya Tilak Marg, Dhobi Talao, Mumbai - 400002<br/>"
        "<b>GST Registration No.:</b> 27AABCR1234R1ZM | <b>State:</b> Maharashtra (27)<br/>"
        "-----------------------------------------------------------------------------------------------------------------<br/>"
        "<b>Bill No:</b> RR-BL-98124 &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; <b>Dated:</b> 05.11.2026<br/>"
        "<b>Buyer GSTIN:</b> 27AAACT9988T1Z1 &nbsp;&nbsp;&nbsp;&nbsp; <b>Place of Supply:</b> 27-Maharashtra"
    )
    story.append(Paragraph(header_text, styles['Normal']))
    story.append(Spacer(1, 15))

    item_data = [
        ["Item Description", "HSN/SAC", "Qty", "Amount"],
        ["Office Stationery & Paper Reams", "480256", "10 Pack", "15,000.00"]
    ]
    t = Table(item_data, colWidths=[240, 100, 80, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4A5568")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (3,0), (3,-1), 'RIGHT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    summary_data = [
        ["Assessable Value:", "15,000.00"],
        ["Central Tax @ 9%:", "1,350.00"],
        ["State Tax @ 9%:", "1,350.00"],
        ["Gross Total (Rs.):", "17,700.00"]
    ]
    st = Table(summary_data, colWidths=[420, 120])
    st.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
    ]))
    story.append(st)
    doc.build(story)


def create_invoice_5_services(output_path: Path):
    """Format C: Corporate IT Services."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>TAX INVOICE</b>", styles['Title']))
    story.append(Spacer(1, 10))

    corp_text = (
        "<b>Tata Consultancy Services Ltd</b><br/>"
        "TCS House, Raveline Street, Fort, Mumbai - 400001<br/>"
        "<b>GSTIN:</b> 27AAACT1234T1Z4 &nbsp;&nbsp;&nbsp;&nbsp; <b>PAN:</b> AAACT1234T<br/>"
        "<br/>"
        "<b>Tax Invoice Number:</b> TCS/2026/099<br/>"
        "<b>Invoice Date:</b> 10-Nov-2026<br/>"
        "<b>Purchase Order:</b> PO-TCS-5512<br/>"
        "<b>Place of Supply:</b> 29-Karnataka<br/>"
        "<b>Recipient GSTIN:</b> 29AABCB1122B1Z3"
    )
    story.append(Paragraph(corp_text, styles['Normal']))
    story.append(Spacer(1, 15))

    item_data = [
        ["Service Description", "SAC Code", "Rate", "Amount (INR)"],
        ["Enterprise ERP Implementation & Support", "998313", "2,50,000.00", "2,50,000.00"]
    ]
    t = Table(item_data, colWidths=[240, 90, 90, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2C7A7B")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    summary_data = [
        ["Sub Total:", "2,50,000.00"],
        ["Integrated Tax @ 18%:", "45,000.00"],
        ["Net Amount Payable (INR):", "2,95,000.00"]
    ]
    st = Table(summary_data, colWidths=[420, 120])
    st.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
    ]))
    story.append(st)
    doc.build(story)


def create_invoice_6_calc_mismatch(output_path: Path):
    """Format E: Test invoice with GST Calculation Mismatch."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>TAX INVOICE (MISMATCH TEST)</b>", styles['Title']))
    story.append(Spacer(1, 10))

    header_text = (
        "<b>Supplier Details:</b> Delta Logistics & Movers Pvt Ltd<br/>"
        "Plot 18, Transport Nagar, Vashi, Navi Mumbai - 400703<br/>"
        "<b>GSTIN:</b> 27AAACD9988D1Z3 | <b>State:</b> Maharashtra (27)<br/>"
        "<b>Invoice No:</b> DL-2026-5501 &nbsp;&nbsp;&nbsp;&nbsp; <b>Invoice Date:</b> 08-11-2026"
    )
    story.append(Paragraph(header_text, styles['Normal']))
    story.append(Spacer(1, 15))

    summary_data = [
        ["Taxable Value:", "40,000.00"],
        ["CGST @ 9%:", "3,600.00"],
        ["SGST @ 9%:", "3,600.00"],
        ["Invoice Total (INR):", "50,000.00"]
    ]
    st = Table(summary_data, colWidths=[400, 140])
    st.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
    ]))
    story.append(st)
    doc.build(story)


def create_invoice_7_invalid_gstin(output_path: Path):
    """Format F: Test invoice with obviously invalid GSTIN."""
    doc = SimpleDocTemplate(str(output_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>TAX INVOICE (INVALID GSTIN TEST)</b>", styles['Title']))
    story.append(Spacer(1, 10))

    header_text = (
        "<b>Supplier Name:</b> QuickFix Hardware Agency<br/>"
        "Station Road, Thane West - 400601<br/>"
        "<b>GSTIN:</b> 99INVALID123 | <b>State:</b> Maharashtra (27)<br/>"
        "<b>Invoice Number:</b> QF-9921 &nbsp;&nbsp;&nbsp;&nbsp; <b>Date:</b> 12-11-2026"
    )
    story.append(Paragraph(header_text, styles['Normal']))
    story.append(Spacer(1, 15))

    summary_data = [
        ["Taxable Value:", "20,000.00"],
        ["CGST @ 9%:", "1,800.00"],
        ["SGST @ 9%:", "1,800.00"],
        ["Invoice Total:", "23,600.00"]
    ]
    st = Table(summary_data, colWidths=[400, 140])
    st.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (0,-1), (-1,-1), 1, colors.black),
    ]))
    story.append(st)
    doc.build(story)


def create_scanned_dummy_invoice(output_path: Path):
    """Format D: Scanned Dummy PDF (Image Only)."""
    img = Image.new('RGB', (800, 1000), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([(20, 20), (780, 980)], outline=(180, 180, 180), width=2)
    draw.text((50, 50), "SCANNED INVOICE (IMAGE ONLY)", fill=(0, 0, 0))
    draw.text((50, 100), "Supplier: ScanCorp Logistics", fill=(50, 50, 50))
    draw.text((50, 130), "GSTIN: 27AABCS9988C1Z2", fill=(50, 50, 50))
    draw.text((50, 160), "Bill No: SC-9923", fill=(50, 50, 50))
    draw.text((50, 190), "Date: 01-11-2026", fill=(50, 50, 50))
    draw.text((50, 240), "Total: Rs. 24,000.00", fill=(0, 0, 0))
    img.save(str(output_path), "PDF", resolution=100.0)


if __name__ == "__main__":
    config.init_directories()
    inv1 = config.INPUT_DIR / "Sample_Invoice_01_IntraState.pdf"
    inv2 = config.INPUT_DIR / "Sample_Invoice_02_InterState.pdf"
    inv3 = config.INPUT_DIR / "Sample_Invoice_03_Scanned_Dummy.pdf"
    inv4 = config.INPUT_DIR / "Sample_Invoice_04_Format_B_Retail.pdf"
    inv5 = config.INPUT_DIR / "Sample_Invoice_05_Format_C_Service.pdf"
    inv6 = config.INPUT_DIR / "Sample_Invoice_06_Tax_Mismatch.pdf"
    inv7 = config.INPUT_DIR / "Sample_Invoice_07_Invalid_GSTIN.pdf"
    inv8 = config.INPUT_DIR / "Sample_Invoice_08_Duplicate_Copy.pdf"

    print("Generating comprehensive sample invoices...")
    create_invoice_1(inv1)
    create_invoice_2(inv2)
    create_scanned_dummy_invoice(inv3)
    create_invoice_4_retail(inv4)
    create_invoice_5_services(inv5)
    create_invoice_6_calc_mismatch(inv6)
    create_invoice_7_invalid_gstin(inv7)

    # Create Duplicate: Copy of Invoice 1 under different filename
    shutil.copy2(inv1, inv8)
    print(f"[+] Created: {inv8.name} (Duplicate copy of Sample_Invoice_01_IntraState.pdf)")

    print("Done! You now have 8 comprehensive test invoices ready.")
