from io import BytesIO
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("PDF feature disabled: reportlab not installed")


def generate_pdf_blob(template_path, data):
    if not REPORTLAB_AVAILABLE:
        return None

    try:
        maintenance = data.get('maintenance', {})
        society     = data.get('society', {})
        user        = data.get('user', {})
        flat        = data.get('flat', {})
        date_today  = data.get('date_today', datetime.now().strftime('%B %d, %Y'))

        # ✅ FIXED: Handle both datetime object and string
        paid_date = maintenance.get('paid_date', '')
        if paid_date and hasattr(paid_date, 'strftime'):
            paid_date = paid_date.strftime('%B %d, %Y %I:%M %p')
        elif paid_date:
            try:
                paid_date = datetime.strptime(
                    str(paid_date), '%Y-%m-%d %H:%M:%S'
                ).strftime('%B %d, %Y %I:%M %p')
            except Exception:
                paid_date = str(paid_date)

        # ✅ FIXED: Clean payment method display
        payment_method = maintenance.get('payment_method', '')
        if not payment_method or payment_method == 'None':
            payment_method = 'N/A'

        buffer = BytesIO()
        doc    = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=50, leftMargin=50,
            topMargin=40, bottomMargin=40
        )

        elements = []

        # ── COLORS ──
        PURPLE     = colors.HexColor('#4e46e5')
        DARK       = colors.HexColor('#0f172a')
        SLATE      = colors.HexColor('#475569')
        LIGHT_GRAY = colors.HexColor('#f8fafc')
        BORDER     = colors.HexColor('#e2e8f0')
        GREEN      = colors.HexColor('#10b981')
        WHITE      = colors.white

        # ── TOP BANNER ──
        banner_data = [[
            Paragraph(
                f'<font size="20"><b>{society.get("name", "SocietyHQ")}</b></font><br/>'
                f'<font size="10" color="#a5b4fc">{society.get("address", "")}</font>',
                ParagraphStyle('banner', fontName='Helvetica',
                               alignment=TA_LEFT, textColor=WHITE, leading=22)
            ),
            Paragraph(
                '<font size="11" color="#a5b4fc">MAINTENANCE</font><br/>'
                '<font size="20"><b>INVOICE</b></font>',
                ParagraphStyle('bannerR', fontName='Helvetica-Bold',
                               alignment=TA_RIGHT, textColor=WHITE, leading=24)
            )
        ]]
        banner_table = Table(banner_data, colWidths=[300, 195])
        banner_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), PURPLE),
            ('TOPPADDING',    (0,0),(-1,-1), 22),
            ('BOTTOMPADDING', (0,0),(-1,-1), 22),
            ('LEFTPADDING',   (0,0),(0,-1),  24),
            ('RIGHTPADDING',  (-1,0),(-1,-1),24),
        ]))
        elements.append(banner_table)
        elements.append(Spacer(1, 25))

        # ── INVOICE META ──
        is_paid = str(maintenance.get('status', '')).lower() == 'paid'
        status_text = (
            '<font size="13" color="#10b981"><b>● PAID</b></font>'
            if is_paid else
            '<font size="13" color="#ef4444"><b>● UNPAID</b></font>'
        )
        meta_data = [[
            Paragraph(
                f'<font size="10" color="#475569">Invoice Date</font><br/>'
                f'<font size="13"><b>{date_today}</b></font>',
                ParagraphStyle('meta', fontName='Helvetica', alignment=TA_LEFT)
            ),
            Paragraph(
                f'<font size="10" color="#475569">Payment Status</font><br/>'
                f'{status_text}',
                ParagraphStyle('metaR', fontName='Helvetica', alignment=TA_RIGHT)
            )
        ]]
        meta_table = Table(meta_data, colWidths=[250, 245])
        meta_table.setStyle(TableStyle([
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 20))
        elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
        elements.append(Spacer(1, 20))

        # ── RESIDENT INFO CARDS ──
        info_items = [
            ('Resident',  user.get('full_name', 'N/A')),
            ('Email',     user.get('email', 'N/A')),
            ('Flat No',   flat.get('flat_number', 'N/A')),
            ('Block',     flat.get('block_name', 'N/A')),
        ]
        info_cells = []
        for label, value in info_items:
            info_cells.append(
                Paragraph(
                    f'<font size="9" color="#94a3b8">{label}</font><br/>'
                    f'<font size="11"><b>{value}</b></font>',
                    ParagraphStyle('infoCell', fontName='Helvetica',
                                   alignment=TA_LEFT, leading=16)
                )
            )
        info_table = Table([info_cells], colWidths=[124, 124, 124, 123])
        info_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), LIGHT_GRAY),
            ('TOPPADDING',    (0,0),(-1,-1), 14),
            ('BOTTOMPADDING', (0,0),(-1,-1), 14),
            ('LEFTPADDING',   (0,0),(-1,-1), 12),
            ('RIGHTPADDING',  (0,0),(-1,-1), 12),
            ('LINEAFTER',     (0,0),(2,-1),  0.5, BORDER),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 25))

        # ── BILL TABLE ──
        bill_header = [
            Paragraph('<b>Description</b>',
                      ParagraphStyle('th', fontName='Helvetica-Bold',
                                     textColor=WHITE, alignment=TA_LEFT, fontSize=11)),
            Paragraph('<b>Period</b>',
                      ParagraphStyle('th2', fontName='Helvetica-Bold',
                                     textColor=WHITE, alignment=TA_CENTER, fontSize=11)),
            Paragraph('<b>Due Date</b>',
                      ParagraphStyle('th3', fontName='Helvetica-Bold',
                                     textColor=WHITE, alignment=TA_CENTER, fontSize=11)),
            Paragraph('<b>Amount</b>',
                      ParagraphStyle('th4', fontName='Helvetica-Bold',
                                     textColor=WHITE, alignment=TA_RIGHT, fontSize=11)),
        ]
        bill_row = [
            Paragraph('Monthly Maintenance',
                      ParagraphStyle('td', fontName='Helvetica', fontSize=10)),
            Paragraph(
                f"{maintenance.get('month', '')} {maintenance.get('year', '')}",
                ParagraphStyle('td2', fontName='Helvetica', fontSize=10,
                               alignment=TA_CENTER)
            ),
            Paragraph(
                str(maintenance.get('due_date', 'N/A')),
                ParagraphStyle('td3', fontName='Helvetica', fontSize=10,
                               alignment=TA_CENTER)
            ),
            Paragraph(
                f"Rs. {float(maintenance.get('amount', 0)):,.2f}",
                ParagraphStyle('td4', fontName='Helvetica-Bold', fontSize=10,
                               alignment=TA_RIGHT,
                               textColor=colors.HexColor('#1e293b'))
            ),
        ]
        bill_table = Table([bill_header, bill_row], colWidths=[200, 90, 100, 105])
        bill_table.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,0), PURPLE),
            ('TOPPADDING',    (0,0),(-1,-1), 13),
            ('BOTTOMPADDING', (0,0),(-1,-1), 13),
            ('LEFTPADDING',   (0,0),(-1,-1), 14),
            ('RIGHTPADDING',  (0,0),(-1,-1), 14),
            ('BACKGROUND',    (0,1),(-1,1), LIGHT_GRAY),
            ('GRID',          (0,0),(-1,-1), 0.5, BORDER),
        ]))
        elements.append(bill_table)
        elements.append(Spacer(1, 10))

        # ── TOTAL ROW ──
        total_table = Table(
            [['', '', 'TOTAL AMOUNT',
              f"Rs. {float(maintenance.get('amount', 0)):,.2f}"]],
            colWidths=[200, 90, 100, 105]
        )
        total_table.setStyle(TableStyle([
            ('FONTNAME',      (2,0),(2,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (2,0),(2,0), 11),
            ('TEXTCOLOR',     (2,0),(2,0), SLATE),
            ('FONTNAME',      (3,0),(3,0), 'Helvetica-Bold'),
            ('FONTSIZE',      (3,0),(3,0), 14),
            ('TEXTCOLOR',     (3,0),(3,0), PURPLE),
            ('ALIGN',         (2,0),(3,0), 'RIGHT'),
            ('TOPPADDING',    (0,0),(-1,-1), 10),
            ('RIGHTPADDING',  (3,0),(3,0), 14),
        ]))
        elements.append(total_table)
        elements.append(Spacer(1, 25))
        elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
        elements.append(Spacer(1, 15))

        # ── PAYMENT CONFIRMATION BOX ──
        if is_paid:
            confirm_data = [[
                Paragraph(
                    f'<b>Payment Confirmed</b><br/>'
                    f'<font size="10" color="#475569">'
                    f'Received on: {paid_date}&nbsp;&nbsp;|&nbsp;&nbsp;'
                    f'Method: {payment_method}'
                    f'</font>',
                    ParagraphStyle('confirm', fontName='Helvetica',
                                   fontSize=11, leading=20,
                                   textColor=colors.HexColor('#065f46'))
                )
            ]]
            confirm_table = Table(confirm_data, colWidths=[495])
            confirm_table.setStyle(TableStyle([
                ('BACKGROUND',    (0,0),(-1,-1), colors.HexColor('#ecfdf5')),
                ('TOPPADDING',    (0,0),(-1,-1), 14),
                ('BOTTOMPADDING', (0,0),(-1,-1), 14),
                ('LEFTPADDING',   (0,0),(-1,-1), 16),
                ('RIGHTPADDING',  (0,0),(-1,-1), 16),
                ('LINEBEFORE',    (0,0),(0,-1),  4, GREEN),
            ]))
            elements.append(confirm_table)
            elements.append(Spacer(1, 20))

        # ── FOOTER ──
        elements.append(Paragraph(
            f'<font color="#94a3b8">This is a computer-generated invoice. '
            f'For queries contact {society.get("name", "society")} management. '
            f'© {datetime.now().year} SocietyHQ</font>',
            ParagraphStyle('footer', fontName='Helvetica',
                           fontSize=8, alignment=TA_CENTER)
        ))

        doc.build(elements)
        return buffer.getvalue()

    except Exception as e:
        print(f"PDF generation error: {e}")
        return None