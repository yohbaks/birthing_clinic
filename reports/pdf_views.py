from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
from accounts.permissions import role_required

# ── Color palette ──────────────────────────────────────────────────────────────
ROSE     = colors.HexColor("#E8527A")
NAVY     = colors.HexColor("#1A2B4B")
TEAL     = colors.HexColor("#2ABFBF")
GRAY     = colors.HexColor("#64748B")
LGRAY    = colors.HexColor("#F0F4F8")
WHITE    = colors.white
BLACK    = colors.black

def _get_clinic_settings():
    try:
        from accounts.models import ClinicSettings
        return ClinicSettings.get()
    except Exception:
        return None

def _clinic_header(elements, title, subtitle=""):
    """Standard clinic letterhead for all PDFs."""
    cs = _get_clinic_settings()
    clinic_name    = cs.clinic_name if cs else "BirthCare Clinic"
    clinic_tagline = cs.clinic_tagline if cs else "Maternity & Newborn Care Services"
    clinic_address = cs.address if cs else ""
    clinic_phone   = cs.contact_number if cs else ""
    clinic_doh     = cs.doh_license if cs else ""
    clinic_ph      = cs.philhealth_accno if cs else ""

    styles = getSampleStyleSheet()
    # Clinic name
    logo = cs.logo_url if cs and cs.logo_url else "🌸"
    elements.append(Paragraph(
        f"<b>{logo} {clinic_name}</b>",
        ParagraphStyle("Brand", fontName="Helvetica-Bold", fontSize=16,
                        spaceAfter=2, alignment=TA_CENTER,
                        textColor=colors.HexColor("#E8527A"))
    ))
    elements.append(Paragraph(
        clinic_tagline,
        ParagraphStyle("Sub", fontName="Helvetica", fontSize=9,
                        textColor=GRAY, spaceAfter=2, alignment=TA_CENTER)
    ))
    if clinic_address:
        elements.append(Paragraph(clinic_address,
            ParagraphStyle("Addr", fontName="Helvetica", fontSize=8,
                            textColor=GRAY, spaceAfter=1, alignment=TA_CENTER)))
    if clinic_phone:
        elements.append(Paragraph(f"Tel: {clinic_phone}",
            ParagraphStyle("Tel", fontName="Helvetica", fontSize=8,
                            textColor=GRAY, spaceAfter=1, alignment=TA_CENTER)))
    accno_parts = []
    if clinic_ph:  accno_parts.append(f"PhilHealth: {clinic_ph}")
    if clinic_doh: accno_parts.append(f"DOH: {clinic_doh}")
    if accno_parts:
        elements.append(Paragraph("  ·  ".join(accno_parts),
            ParagraphStyle("Acc", fontName="Helvetica", fontSize=7,
                            textColor=GRAY, spaceAfter=3, alignment=TA_CENTER)))
    elements.append(HRFlowable(width="100%", thickness=2, color=ROSE, spaceAfter=8))
    if title:
        elements.append(Paragraph(title.upper(),
            ParagraphStyle("DocTitle", fontName="Helvetica-Bold", fontSize=13,
                            textColor=NAVY, spaceBefore=4, spaceAfter=2,
                            alignment=TA_CENTER)))
    if subtitle:
        elements.append(Paragraph(subtitle,
            ParagraphStyle("DocSub", fontName="Helvetica", fontSize=9,
                            textColor=GRAY, spaceAfter=10, alignment=TA_CENTER)))
    elements.append(Spacer(1, 0.1*inch))

def _field_table(data, col_widths=None):
    """Two-column label-value table."""
    if col_widths is None:
        col_widths = [2.0*inch, 3.5*inch]
    tbl = Table(data, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), GRAY),
        ("TEXTCOLOR", (1,0), (1,-1), NAVY),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [WHITE, colors.HexColor("#FAFBFC")]),
        ("GRID",      (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
        ("TOPPADDING",(0,0),(-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING",(0,0),(-1,-1), 8),
    ]))
    return tbl

def _section_header(text):
    return Paragraph(text.upper(),
        ParagraphStyle("SecHdr", fontName="Helvetica-Bold", fontSize=8,
                        textColor=ROSE, spaceBefore=12, spaceAfter=4,
                        borderPad=4, backColor=colors.HexColor("#FFF0F3"),
                        borderWidth=0, leftIndent=0))

def _pdf_response(filename):
    resp = HttpResponse(content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


# ── 1. PATIENT SUMMARY CARD ────────────────────────────────────────────────────
@login_required
@role_required('clinical')
def pdf_patient_summary(request, pk):
    from patients.models import Patient
    from prenatal.models import PrenatalVisit, UltrasoundRecord
    from delivery.models import DeliveryRecord
    patient = get_object_or_404(Patient, pk=pk)

    resp = _pdf_response(f"patient_{patient.record_number}.pdf")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=2*cm)
    E = []
    _clinic_header(E, "Patient Summary Card",
                   f"Generated {timezone.now().strftime('%B %d, %Y %H:%M')}")

    # Patient ID badge
    E.append(_section_header("Patient Information"))
    E.append(_field_table([
        ["Record Number:",  patient.record_number],
        ["Full Name:",      patient.full_name],
        ["Date of Birth:",  patient.date_of_birth.strftime("%B %d, %Y") if patient.date_of_birth else "—"],
        ["Age:",            f"{patient.age} years old"],
        ["Civil Status:",   patient.get_civil_status_display()],
        ["Blood Type:",     patient.blood_type or "Unknown"],
        ["Contact:",        patient.contact_number],
        ["Address:",        patient.address],
        ["Partner/Husband:",patient.partner_name or "—"],
    ]))

    E.append(_section_header("Obstetric History"))
    E.append(_field_table([
        ["G/P/A:",          f"G{patient.gravida}  P{patient.para}  A{patient.abortion_history}"],
        ["LMP:",            patient.lmp.strftime("%B %d, %Y") if patient.lmp else "—"],
        ["EDD:",            patient.edd.strftime("%B %d, %Y") if patient.edd else "—"],
        ["Risk Level:",     patient.get_risk_level_display()],
        ["Allergies:",      patient.allergies or "NKDA"],
        ["Conditions:",     patient.existing_conditions or "None"],
    ]))

    # Emergency contacts
    contacts = patient.emergency_contacts.all()
    if contacts:
        E.append(_section_header("Emergency Contacts"))
        ec_data = [["Name", "Relationship", "Contact #"]]
        for ec in contacts:
            ec_data.append([ec.name, ec.relationship, ec.contact_number])
        ec_tbl = Table(ec_data, colWidths=[2.5*inch, 2*inch, 2*inch])
        ec_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), ROSE),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
            ("TOPPADDING",  (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("LEFTPADDING", (0,0),(-1,-1), 6),
        ]))
        E.append(ec_tbl)

    # Recent prenatal visits
    visits = patient.prenatal_visits.order_by("-visit_date")[:5]
    if visits:
        E.append(_section_header("Recent Prenatal Visits"))
        v_data = [["Date", "GA (wks)", "BP", "Weight", "FHR", "Risk"]]
        for v in visits:
            v_data.append([
                v.visit_date.strftime("%m/%d/%Y"),
                str(v.gestational_age_weeks),
                v.bp_display,
                f"{v.weight} kg",
                str(v.fetal_heart_rate) if v.fetal_heart_rate else "—",
                v.get_risk_flag_display(),
            ])
        v_tbl = Table(v_data, colWidths=[1.1*inch, 0.9*inch, 1.0*inch, 0.9*inch, 0.8*inch, 1.3*inch])
        v_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), NAVY),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
            ("TOPPADDING",  (0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
            ("LEFTPADDING", (0,0),(-1,-1), 5),
        ]))
        E.append(v_tbl)

    if patient.notes:
        E.append(_section_header("Clinical Notes"))
        E.append(Paragraph(patient.notes,
            ParagraphStyle("Notes", fontName="Helvetica", fontSize=9,
                            textColor=NAVY, leading=14)))

    E.append(Spacer(1, 0.3*inch))
    E.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    E.append(Paragraph(
        f"Generated by BirthCare System · {timezone.now().strftime('%B %d, %Y %H:%M')} · {request.user.get_full_name() or request.user.username}",
        ParagraphStyle("Footer", fontName="Helvetica", fontSize=7, textColor=GRAY,
                        alignment=TA_CENTER, spaceBefore=4)))

    doc.build(E)
    resp.write(buf.getvalue())
    return resp


# ── 2. PRENATAL VISIT RECORD (PDF) ────────────────────────────────────────────
@login_required
@role_required('clinical')
def pdf_prenatal_visit(request, pk):
    from prenatal.models import PrenatalVisit
    visit = get_object_or_404(PrenatalVisit, pk=pk)

    resp = _pdf_response(f"prenatal_{visit.patient.record_number}_{visit.visit_date}.pdf")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=2*cm)
    E = []
    _clinic_header(E, "Prenatal Visit Record",
                   f"Visit Date: {visit.visit_date.strftime('%B %d, %Y')}")

    E.append(_section_header("Patient Information"))
    E.append(_field_table([
        ["Patient:",       visit.patient.full_name],
        ["Record No.:",    visit.patient.record_number],
        ["G/P/A:",         f"G{visit.patient.gravida}  P{visit.patient.para}  A{visit.patient.abortion_history}"],
        ["EDD:",           visit.patient.edd.strftime("%B %d, %Y") if visit.patient.edd else "—"],
    ]))

    E.append(_section_header("Vital Signs & Measurements"))
    # 2-column vitals layout
    vitals_data = [
        ["Gestational Age:",   f"{visit.gestational_age_weeks} weeks",
         "Blood Pressure:",    visit.bp_display + (" ⚠ HIGH" if visit.is_bp_high else "")],
        ["Weight:",            f"{visit.weight} kg",
         "Temperature:",       f"{visit.temperature} °C"],
        ["Fetal Heart Rate:",  f"{visit.fetal_heart_rate} bpm" if visit.fetal_heart_rate else "—",
         "Fundal Height:",     f"{visit.fundal_height} cm" if visit.fundal_height else "—"],
        ["Risk Flag:",         visit.get_risk_flag_display(),
         "Follow-up Date:",    visit.follow_up_date.strftime("%B %d, %Y") if visit.follow_up_date else "—"],
    ]
    vitals_tbl = Table(vitals_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 2.0*inch])
    vitals_tbl.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), GRAY),
        ("TEXTCOLOR", (2,0), (2,-1), GRAY),
        ("TEXTCOLOR", (1,0), (1,-1), NAVY),
        ("TEXTCOLOR", (3,0), (3,-1), NAVY),
        ("GRID",      (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE, LGRAY]),
        ("TOPPADDING",(0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",(0,0),(-1,-1), 7),
    ]))
    E.append(vitals_tbl)

    for label, text in [
        ("Chief Complaint", visit.chief_complaint),
        ("Assessment",      visit.assessment),
        ("Plan",            visit.plan),
        ("Prescribed Medicines", visit.prescribed_medicines),
        ("Notes",           visit.notes),
    ]:
        if text:
            E.append(_section_header(label))
            E.append(Paragraph(text, ParagraphStyle("Body", fontName="Helvetica",
                                fontSize=9, textColor=NAVY, leading=14,
                                spaceAfter=4)))

    # Lab requests
    labs = visit.lab_requests.all()
    if labs:
        E.append(_section_header("Lab Requests"))
        lab_data = [["Test Name", "Result", "Date", "Notes"]]
        for lr in labs:
            lab_data.append([
                lr.test_name,
                lr.result or "Pending",
                lr.result_date.strftime("%m/%d/%Y") if lr.result_date else "—",
                lr.notes or "—",
            ])
        lab_tbl = Table(lab_data, colWidths=[1.8*inch, 2.0*inch, 1.0*inch, 1.7*inch])
        lab_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), TEAL),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
            ("TOPPADDING",  (0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
            ("LEFTPADDING", (0,0),(-1,-1), 5),
        ]))
        E.append(lab_tbl)

    # Signature lines
    E.append(Spacer(1, 0.5*inch))
    sig_data = [["", "", ""]]
    sig_tbl = Table(sig_data, colWidths=[2.5*inch, 1.0*inch, 2.5*inch])
    sig_tbl.setStyle(TableStyle([
        ("LINEABOVE", (0,0), (0,0), 1, NAVY),
        ("LINEABOVE", (2,0), (2,0), 1, NAVY),
        ("FONTNAME",  (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 8),
        ("TEXTCOLOR", (0,0), (-1,-1), GRAY),
        ("ALIGN",     (0,0), (-1,-1), "CENTER"),
    ]))
    E.append(Table(
        [["Attending Staff Signature", "", "Patient / Guardian Signature"]],
        colWidths=[2.5*inch, 1.0*inch, 2.5*inch],
        style=TableStyle([
            ("FONTNAME", (0,0),(-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0),(-1,-1), 8),
            ("TEXTCOLOR",(0,0),(-1,-1), GRAY),
            ("ALIGN",    (0,0),(-1,-1), "CENTER"),
        ])
    ))

    E.append(Spacer(1, 0.2*inch))
    E.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    E.append(Paragraph(
        f"BirthCare Clinic · Prenatal Visit Record · {visit.patient.record_number} · {timezone.now().strftime('%B %d, %Y')}",
        ParagraphStyle("Footer", fontName="Helvetica", fontSize=7, textColor=GRAY,
                        alignment=TA_CENTER, spaceBefore=4)))

    doc.build(E)
    resp.write(buf.getvalue())
    return resp


# ── 3. DELIVERY CERTIFICATE ────────────────────────────────────────────────────
@login_required
@role_required('clinical')
def pdf_delivery_certificate(request, pk):
    from delivery.models import DeliveryRecord
    delivery = get_object_or_404(DeliveryRecord, pk=pk)

    resp = _pdf_response(f"delivery_cert_{delivery.patient.record_number}.pdf")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=2*cm)
    E = []
    _clinic_header(E, "Delivery Summary Record",
                   f"Admission: {delivery.admission_datetime.strftime('%B %d, %Y %H:%M') if delivery.admission_datetime else '—'}")

    E.append(_section_header("Patient Information"))
    E.append(_field_table([
        ["Patient:",        delivery.patient.full_name],
        ["Record No.:",     delivery.patient.record_number],
        ["Age:",            f"{delivery.patient.age} years"],
        ["G/P/A:",          f"G{delivery.patient.gravida}  P{delivery.patient.para}  A{delivery.patient.abortion_history}"],
        ["Blood Type:",     delivery.patient.blood_type or "Unknown"],
        ["Address:",        delivery.patient.address],
    ]))

    E.append(_section_header("Delivery Information"))
    E.append(_field_table([
        ["Admission Date/Time:",  delivery.admission_datetime.strftime("%B %d, %Y %H:%M") if delivery.admission_datetime else "—"],
        ["Delivery Date/Time:",   delivery.delivery_datetime.strftime("%B %d, %Y %H:%M") if delivery.delivery_datetime else "—"],
        ["Discharge Date/Time:",  delivery.discharge_datetime.strftime("%B %d, %Y %H:%M") if delivery.discharge_datetime else "—"],
        ["Delivery Type:",        delivery.get_delivery_type_display() if delivery.delivery_type else "—"],
        ["Presentation:",         delivery.presentation.title() if delivery.presentation else "—"],
        ["Attending Midwife:",    delivery.attending_midwife.get_full_name() if delivery.attending_midwife else "—"],
        ["Attending Doctor:",     delivery.attending_doctor.get_full_name() if delivery.attending_doctor else "—"],
        ["EBL (mL):",             str(delivery.estimated_blood_loss) if delivery.estimated_blood_loss else "—"],
        ["Complications:",        delivery.complications or "None noted"],
        ["Maternal Condition:",   delivery.maternal_condition or "—"],
    ]))

    # Newborns
    newborns = delivery.newborns.all()
    if newborns:
        E.append(_section_header("Newborn(s)"))
        nb_data = [["Baby ID", "Name", "Gender", "Birth Time", "Weight", "APGAR 1/5", "Status"]]
        for nb in newborns:
            nb_data.append([
                nb.baby_id,
                nb.baby_name or "—",
                nb.get_gender_display(),
                nb.birth_datetime.strftime("%H:%M") if nb.birth_datetime else "—",
                f"{nb.weight_grams}g",
                f"{nb.apgar_1min or '—'}/{nb.apgar_5min or '—'}",
                nb.get_birth_status_display(),
            ])
        nb_tbl = Table(nb_data, colWidths=[0.9*inch, 1.2*inch, 0.7*inch, 0.9*inch, 0.8*inch, 0.8*inch, 0.7*inch])
        nb_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#065F46")),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
            ("TOPPADDING",  (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("LEFTPADDING", (0,0),(-1,-1), 5),
        ]))
        E.append(nb_tbl)

    # Referral info
    if delivery.referral_hospital:
        E.append(_section_header("Referral Information"))
        E.append(_field_table([
            ["Referred To:", delivery.referral_hospital],
            ["Reason:",      delivery.referral_reason or "—"],
        ]))

    # Signature block
    E.append(Spacer(1, 0.6*inch))
    sig_rows = [[
        Paragraph("______________________________<br/><font size=8 color='#64748B'>Attending Midwife / Nurse</font>", 
                  ParagraphStyle("Sig", fontName="Helvetica", fontSize=9, alignment=TA_CENTER)),
        Paragraph("", ParagraphStyle("Gap", fontSize=9)),
        Paragraph("______________________________<br/><font size=8 color='#64748B'>Attending Physician</font>",
                  ParagraphStyle("Sig", fontName="Helvetica", fontSize=9, alignment=TA_CENTER)),
    ]]
    sig_tbl = Table(sig_rows, colWidths=[2.5*inch, 1.0*inch, 2.5*inch])
    E.append(sig_tbl)

    E.append(Spacer(1, 0.3*inch))
    E.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    E.append(Paragraph(
        f"BirthCare Clinic · Delivery Record · {delivery.patient.record_number} · {timezone.now().strftime('%B %d, %Y')}",
        ParagraphStyle("Footer", fontName="Helvetica", fontSize=7, textColor=GRAY,
                        alignment=TA_CENTER, spaceBefore=4)))

    doc.build(E)
    resp.write(buf.getvalue())
    return resp


# ── 4. STATEMENT OF ACCOUNT / OFFICIAL RECEIPT (PDF) ─────────────────────────
@login_required
@role_required('billing_view')
def pdf_soa(request, pk):
    from billing.models import Bill
    bill = get_object_or_404(Bill, pk=pk)
    payments = bill.payments.all().order_by("payment_date")
    items = bill.bill_items.all()

    resp = _pdf_response(f"SOA_{bill.bill_number}.pdf")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=2*cm)
    E = []
    _clinic_header(E, "Statement of Account",
                   f"Bill No.: {bill.bill_number}   Date: {bill.billing_date.strftime('%B %d, %Y')}")

    E.append(_section_header("Patient Information"))
    E.append(_field_table([
        ["Patient:",       bill.patient.full_name],
        ["Record No.:",    bill.patient.record_number],
        ["Contact:",       bill.patient.contact_number],
        ["Address:",       bill.patient.address],
    ], col_widths=[1.8*inch, 4.0*inch]))

    # Bill items
    E.append(_section_header("Charges"))
    item_data = [["Description", "Type", "Qty", "Unit Price", "Total"]]
    for bi in items:
        item_data.append([
            bi.description,
            bi.get_item_type_display(),
            str(bi.quantity),
            f"P{bi.unit_price:,.2f}",
            f"P{bi.total_price:,.2f}",
        ])
    item_tbl = Table(item_data, colWidths=[2.5*inch, 1.0*inch, 0.5*inch, 1.0*inch, 1.0*inch])
    item_tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,0), ROSE),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ALIGN",       (2,0), (-1,-1), "RIGHT"),
        ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING", (0,0),(-1,-1), 6),
    ]))
    E.append(item_tbl)

    # Totals block
    E.append(Spacer(1, 0.15*inch))
    total_rows = [
        ["", "Subtotal:", f"P{bill.subtotal:,.2f}"],
    ]
    if bill.discount:
        total_rows.append(["", f"Discount ({bill.discount_reason or ''}):", f"-P{bill.discount:,.2f}"])
    total_rows.append(["", "TOTAL AMOUNT:", f"P{bill.total_amount:,.2f}"])
    total_rows.append(["", "Total Paid:", f"P{bill.amount_paid:,.2f}"])
    total_rows.append(["", "BALANCE DUE:", f"P{bill.balance:,.2f}"])

    tot_tbl = Table(total_rows, colWidths=[3.5*inch, 1.5*inch, 1.0*inch])
    tot_style = TableStyle([
        ("FONTNAME",    (1,0), (1,-1), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 9),
        ("ALIGN",       (1,0), (-1,-1), "RIGHT"),
        ("TEXTCOLOR",   (1,0), (1,-1), GRAY),
        ("TEXTCOLOR",   (2,0), (2,-1), NAVY),
        ("TOPPADDING",  (0,0),(-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ])
    # Highlight TOTAL and BALANCE rows
    tot_style.add("FONTNAME", (1,len(total_rows)-3), (-1,len(total_rows)-3), "Helvetica-Bold")
    tot_style.add("FONTSIZE", (1,len(total_rows)-3), (-1,len(total_rows)-3), 10)
    tot_style.add("BACKGROUND",(0,len(total_rows)-1),(-1,len(total_rows)-1), colors.HexColor("#FEE2E2"))
    tot_style.add("FONTNAME",  (0,len(total_rows)-1),(-1,len(total_rows)-1), "Helvetica-Bold")
    tot_style.add("TEXTCOLOR", (2,len(total_rows)-1),(2,len(total_rows)-1), colors.HexColor("#DC2626"))
    tot_style.add("FONTSIZE",  (0,len(total_rows)-1),(-1,len(total_rows)-1), 11)
    tot_tbl.setStyle(tot_style)
    E.append(tot_tbl)

    # Payment history
    if payments:
        E.append(_section_header("Payment History"))
        pay_data = [["OR Number", "Date", "Amount", "Method", "Reference"]]
        for pay in payments:
            pay_data.append([
                pay.receipt_number,
                pay.payment_date.strftime("%m/%d/%Y %H:%M"),
                f"P{pay.amount:,.2f}",
                pay.get_payment_method_display(),
                pay.reference_number or "—",
            ])
        pay_tbl = Table(pay_data, colWidths=[1.2*inch, 1.4*inch, 1.0*inch, 1.1*inch, 1.3*inch])
        pay_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#065F46")),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("ALIGN",       (2,0), (2,-1), "RIGHT"),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
            ("TOPPADDING",  (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("LEFTPADDING", (0,0),(-1,-1), 5),
        ]))
        E.append(pay_tbl)

    # Cashier signature + status stamp
    E.append(Spacer(1, 0.5*inch))
    status_color = colors.HexColor("#059669") if bill.payment_status == "paid" else colors.HexColor("#DC2626")
    E.append(Paragraph(
        f"<font color='{status_color.hexval()}'>■</font> <b>Payment Status: {bill.get_payment_status_display().upper()}</b>",
        ParagraphStyle("Status", fontName="Helvetica-Bold", fontSize=12, alignment=TA_CENTER)))

    E.append(Spacer(1, 0.3*inch))
    E.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    E.append(Paragraph(
        f"BirthCare Clinic · SOA · {bill.bill_number} · Generated {timezone.now().strftime('%B %d, %Y %H:%M')}",
        ParagraphStyle("Footer", fontName="Helvetica", fontSize=7, textColor=GRAY,
                        alignment=TA_CENTER, spaceBefore=4)))

    doc.build(E)
    resp.write(buf.getvalue())
    return resp


# ── 5. NEWBORN RECORD PDF ─────────────────────────────────────────────────────
@login_required
@role_required('clinical')
def pdf_newborn_record(request, pk):
    from newborn.models import NewbornRecord
    nb = get_object_or_404(NewbornRecord, pk=pk)
    immunizations = nb.immunizations.all().order_by("date_given")

    resp = _pdf_response(f"newborn_{nb.baby_id}.pdf")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                             leftMargin=1.5*cm, rightMargin=1.5*cm,
                             topMargin=1.5*cm, bottomMargin=2*cm)
    E = []
    _clinic_header(E, "Newborn Record",
                   f"Baby ID: {nb.baby_id}")

    E.append(_section_header("Newborn Information"))
    E.append(_field_table([
        ["Baby Name:",       nb.baby_name or "—"],
        ["Baby ID:",         nb.baby_id],
        ["Gender:",          nb.get_gender_display()],
        ["Birth Status:",    nb.get_birth_status_display()],
        ["Date & Time:",     nb.birth_datetime.strftime("%B %d, %Y %H:%M") if nb.birth_datetime else "—"],
        ["Weight:",          f"{nb.weight_grams}g ({nb.weight_kg} kg)"],
        ["Length:",          f"{nb.length_cm} cm"],
        ["Head Circ.:",      f"{nb.head_circumference_cm} cm" if nb.head_circumference_cm else "—"],
        ["APGAR 1 min:",     f"{nb.apgar_1min}/10" if nb.apgar_1min is not None else "—"],
        ["APGAR 5 min:",     f"{nb.apgar_5min}/10" if nb.apgar_5min is not None else "—"],
    ]))

    E.append(_section_header("Initial Interventions"))
    E.append(_field_table([
        ["Vitamin K:",           "✓ Given" if nb.vitamin_k_given else "✗ Not given"],
        ["Eye Prophylaxis:",     "✓ Given" if nb.eye_prophylaxis_given else "✗ Not given"],
        ["Newborn Screening:",   "✓ Done" if nb.newborn_screening_done else "✗ Not done"],
    ]))

    E.append(_section_header("Mother Information"))
    E.append(_field_table([
        ["Mother:",          nb.mother.full_name],
        ["Record No.:",      nb.mother.record_number],
        ["Blood Type:",      nb.mother.blood_type or "Unknown"],
        ["G/P/A:",           f"G{nb.mother.gravida}  P{nb.mother.para}  A{nb.mother.abortion_history}"],
    ]))

    if immunizations:
        E.append(_section_header("Immunizations"))
        imm_data = [["Vaccine", "Date Given", "Dose", "Administered By"]]
        for imm in immunizations:
            imm_data.append([
                imm.vaccine_name,
                imm.date_given.strftime("%m/%d/%Y") if imm.date_given else "—",
                imm.dose or "—",
                imm.administered_by or "—",
            ])
        imm_tbl = Table(imm_data, colWidths=[2.2*inch, 1.1*inch, 1.1*inch, 1.6*inch])
        imm_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0,0), (-1,0), colors.HexColor("#065F46")),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 9),
            ("GRID",        (0,0), (-1,-1), 0.3, colors.HexColor("#E2E8F0")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LGRAY]),
            ("TOPPADDING",  (0,0),(-1,-1), 4),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("LEFTPADDING", (0,0),(-1,-1), 5),
        ]))
        E.append(imm_tbl)

    if nb.notes:
        E.append(_section_header("Notes"))
        E.append(Paragraph(nb.notes, ParagraphStyle("Body", fontName="Helvetica",
                            fontSize=9, textColor=NAVY, leading=14)))

    if nb.discharge_datetime:
        E.append(_section_header("Discharge"))
        E.append(_field_table([
            ["Discharge Date/Time:", nb.discharge_datetime.strftime("%B %d, %Y %H:%M")],
            ["Discharge Weight:",    f"{nb.discharge_weight_grams}g" if nb.discharge_weight_grams else "—"],
        ]))

    E.append(Spacer(1, 0.3*inch))
    E.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
    E.append(Paragraph(
        f"BirthCare Clinic · Newborn Record · {nb.baby_id} · {timezone.now().strftime('%B %d, %Y')}",
        ParagraphStyle("Footer", fontName="Helvetica", fontSize=7, textColor=GRAY,
                        alignment=TA_CENTER, spaceBefore=4)))

    doc.build(E)
    resp.write(buf.getvalue())
    return resp
