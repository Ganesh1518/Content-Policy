"""
generate_corpus.py
-------------------
Builds a SYNTHETIC corpus of hospital operational policies, infection-control
SOPs, patient-safety protocols, consent procedures, and a compliance manual.

Rule compliance:
- Synthetic-Data Rule: every fact below is invented for this exercise. No real
  patient, staff, or institutional data of any kind is used.
- Each document is written with numbered clauses (Section N.M) so the
  ingestion module can attach a stable `clause_id` to every chunk, which is
  required for clause-level citation (AC-02, AC-06).

Run:
    python scripts/generate_corpus.py
Produces >= 30 files under data/corpus/*.md, each with YAML frontmatter:
    doc_id, doc_type, title, effective_date, owner_role
"""

import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "corpus")
os.makedirs(OUT_DIR, exist_ok=True)


def doc(doc_id, doc_type, title, owner_role, effective_date, clauses):
    """clauses: list of (clause_id, heading, body_text)"""
    front = (
        f"---\n"
        f"doc_id: {doc_id}\n"
        f"doc_type: {doc_type}\n"
        f"title: \"{title}\"\n"
        f"owner_role: \"{owner_role}\"\n"
        f"effective_date: {effective_date}\n"
        f"---\n\n"
    )
    body = f"# {title}\n\n"
    for clause_id, heading, text in clauses:
        body += f"## {clause_id} {heading}\n\n{text}\n\n"
    path = os.path.join(OUT_DIR, f"{doc_id}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(front + body)
    return path


DOCS = []

# ---------------------------------------------------------------------------
# 1. Infection control (5 documents)
# ---------------------------------------------------------------------------
DOCS.append(doc(
    "POL-IC-001", "policy", "Hand Hygiene Policy", "Infection Control Officer", "2025-01-10",
    [
        ("3.1", "Purpose", "This policy defines the mandatory hand-hygiene technique and timing "
         "for all clinical staff to reduce healthcare-associated infection (HAI) transmission "
         "within the facility."),
        ("3.2", "The Five Moments", "Staff must perform hand hygiene at five moments: (1) before "
         "touching a patient, (2) before a clean or aseptic procedure, (3) after body-fluid "
         "exposure risk, (4) after touching a patient, and (5) after touching patient surroundings."),
        ("3.3", "Technique", "Alcohol-based hand rub (ABHR) must be applied for a minimum of 20 "
         "seconds covering all hand surfaces. Soap-and-water hand washing is required when hands "
         "are visibly soiled and must last a minimum of 40 seconds."),
        ("3.4", "Pre-Procedure Hand Hygiene", "Before any invasive or aseptic procedure, staff must "
         "perform surgical hand antisepsis using a chlorhexidine-based scrub for a minimum of 2 "
         "minutes, followed by ABHR immediately before glove donning."),
        ("3.5", "Monitoring", "Hand-hygiene compliance is audited monthly by the Infection Control "
         "Officer using direct observation. Compliance below 85% triggers a unit-level retraining "
         "session within 10 working days."),
    ],
))

DOCS.append(doc(
    "SOP-IC-002", "sop", "Personal Protective Equipment (PPE) Donning and Doffing SOP",
    "Infection Control Officer", "2025-01-15",
    [
        ("4.1", "Scope", "Applies to all staff entering isolation rooms or performing aerosol-"
         "generating procedures."),
        ("4.2", "Donning Sequence", "The donning sequence is: (1) perform hand hygiene, (2) gown, "
         "(3) N95/FFP2 respirator with seal check, (4) eye protection or face shield, (5) gloves "
         "pulled over gown cuffs."),
        ("4.3", "Doffing Sequence", "The doffing sequence is: (1) gloves, (2) hand hygiene, (3) "
         "gown, (4) hand hygiene, (5) eye protection, (6) respirator, (7) hand hygiene. Doffing "
         "must occur at the anteroom, never inside the patient room, except for the respirator."),
        ("4.4", "Responsible Role", "The charge nurse on shift is responsible for verifying correct "
         "PPE sequencing for new or agency staff before they enter an isolation room."),
        ("4.5", "Escalation", "Any suspected PPE breach (e.g., torn glove, respirator dislodgement) "
         "must be reported to the Infection Control Officer within 1 hour via the incident-reporting "
         "system described in SOP-IC-004."),
    ],
))

DOCS.append(doc(
    "SOP-IC-003", "sop", "Isolation Precautions SOP", "Infection Control Officer", "2025-02-01",
    [
        ("2.1", "Precaution Categories", "Three precaution categories apply: Contact, Droplet, and "
         "Airborne. Each category has a distinct signage color and PPE requirement posted at the "
         "room entrance."),
        ("2.2", "Contact Precautions", "Used for multidrug-resistant organisms (MDRO). Requires gown "
         "and gloves for all room entry; dedicated or disposable equipment is required."),
        ("2.3", "Droplet Precautions", "Used for pathogens transmitted via respiratory droplets. "
         "Requires a surgical mask within 1 meter of the patient and closed doors are not required."),
        ("2.4", "Airborne Precautions", "Used for pathogens capable of long-distance airborne spread. "
         "Requires a negative-pressure room and a fit-tested N95/FFP2 respirator for all entrants."),
        ("2.5", "Duration", "Precautions remain in effect until the attending physician documents "
         "clinical resolution or until two consecutive negative test results are recorded, per the "
         "organism-specific protocol maintained by Infection Control."),
    ],
))

DOCS.append(doc(
    "SOP-IC-004", "sop", "Infection-Related Incident Reporting SOP", "Infection Control Officer",
    "2025-02-10",
    [
        ("5.1", "Trigger Events", "A reportable infection-control incident includes: a PPE breach, "
         "a needlestick injury, a sharps-disposal violation, or a suspected HAI cluster of two or "
         "more cases in the same unit within 7 days."),
        ("5.2", "Reporting Timeline", "Staff must report the incident within 1 hour of discovery "
         "through the electronic incident form. The Infection Control Officer must acknowledge the "
         "report within 4 hours."),
        ("5.3", "Responsible Role", "The unit charge nurse files the initial report; the Infection "
         "Control Officer conducts the root-cause review within 5 working days."),
        ("5.4", "Escalation Threshold", "A suspected cluster of three or more cases escalates "
         "automatically to the Hospital Safety Committee and must be logged in the compliance "
         "manual per COMP-005 section 6.2."),
    ],
))

DOCS.append(doc(
    "POL-IC-005", "policy", "Environmental Cleaning and Disinfection Policy",
    "Environmental Services Manager", "2025-01-20",
    [
        ("6.1", "Cleaning Frequency", "Patient rooms are terminally cleaned at discharge and "
         "spot-cleaned every 8 hours during occupancy. High-touch surfaces are disinfected every "
         "4 hours in isolation rooms."),
        ("6.2", "Disinfectant Standard", "Only hospital-approved, EPA-listed disinfectants with a "
         "documented contact time are permitted. Contact time must be verified against the product "
         "label before the surface is considered disinfected."),
        ("6.3", "Responsible Role", "Environmental Services staff perform cleaning; the unit charge "
         "nurse verifies terminal cleaning completion before a new admission is accepted into the "
         "room."),
    ],
))

# ---------------------------------------------------------------------------
# 2. Patient safety protocols (6 documents)
# ---------------------------------------------------------------------------
DOCS.append(doc(
    "SOP-PS-101", "sop", "Patient Identification SOP", "Chief Nursing Officer", "2025-01-05",
    [
        ("2.1", "Two-Identifier Rule", "Before any medication administration, specimen collection, "
         "or procedure, staff must verify at least two identifiers: full name and date of birth. "
         "Room number is not an acceptable identifier."),
        ("2.2", "Wristband Requirement", "Every admitted patient must wear an identification "
         "wristband. A missing or illegible wristband must be replaced before the next clinical "
         "task proceeds."),
        ("2.3", "Responsible Role", "The bedside nurse is responsible for identity verification "
         "immediately prior to each clinical task."),
    ],
))

DOCS.append(doc(
    "SOP-PS-102", "sop", "Fall Risk Assessment and Prevention SOP", "Chief Nursing Officer",
    "2025-01-08",
    [
        ("3.1", "Assessment Timing", "A fall-risk score must be calculated at admission, after any "
         "change in patient condition, and every 12 hours during the inpatient stay."),
        ("3.2", "High-Risk Interventions", "Patients scoring high risk require a yellow wristband, "
         "bed alarm activation, and hourly rounding documented in the chart."),
        ("3.3", "Responsible Role", "The admitting nurse performs the initial assessment; each "
         "shift nurse re-scores at handover."),
        ("3.4", "Post-Fall Procedure", "After any fall, the nurse must: (1) assess for injury, (2) "
         "notify the attending physician, (3) complete an incident report within 1 hour, and (4) "
         "reassess fall risk before the patient is left unattended again."),
    ],
))

DOCS.append(doc(
    "SOP-PS-103", "sop", "Medication Administration Safety SOP", "Chief Pharmacy Officer",
    "2025-01-12",
    [
        ("4.1", "Five Rights", "Every medication pass must confirm the right patient, right drug, "
         "right dose, right route, and right time before administration."),
        ("4.2", "High-Alert Medications", "High-alert medications (e.g., insulin, anticoagulants, "
         "opioids) require independent double-check by a second licensed nurse before "
         "administration."),
        ("4.3", "Documentation", "Administration must be documented in the electronic medication "
         "administration record (eMAR) within 15 minutes of the dose being given."),
        ("4.4", "Responsible Role", "The administering nurse and the co-signing nurse are jointly "
         "responsible for the double-check on high-alert medications."),
        ("4.5", "Error Reporting", "Any medication error, including a near-miss, must be reported "
         "through the incident system described in COMP-005 within 1 hour of discovery."),
    ],
))

DOCS.append(doc(
    "SOP-PS-104", "sop", "Surgical Site Verification (Time-Out) SOP", "Chief of Surgery",
    "2025-01-18",
    [
        ("2.1", "Pre-Incision Time-Out", "Immediately before incision, the full surgical team must "
         "pause and verbally confirm patient identity, procedure, surgical site, and site marking."),
        ("2.2", "Site Marking", "The operating surgeon marks the surgical site with the patient "
         "awake and participating, before transfer to the operating room, using an indelible "
         "marker with the surgeon's initials."),
        ("2.3", "Responsible Role", "The circulating nurse leads the verbal time-out checklist; the "
         "surgeon must verbally confirm each item before the first incision."),
        ("2.4", "Documentation", "The completed time-out checklist is scanned into the patient "
         "record within 30 minutes of procedure start."),
    ],
))

DOCS.append(doc(
    "SOP-PS-105", "sop", "Critical Lab Value Notification SOP", "Chief Medical Officer", "2025-01-22",
    [
        ("3.1", "Critical Value Definition", "A critical value is any laboratory result that falls "
         "outside the facility-defined critical range (e.g., serum potassium below 2.5 mmol/L or "
         "above 6.5 mmol/L) and requires immediate clinical action."),
        ("3.2", "Notification Timeline", "The laboratory must notify the ordering clinician or "
         "covering nurse within 30 minutes of a critical value being verified."),
        ("3.3", "Read-Back Requirement", "The receiving clinician must read back the value and the "
         "patient identifier to the laboratory technologist before the call ends."),
        ("3.4", "Responsible Role", "The laboratory technologist initiates notification; the "
         "receiving nurse documents the read-back and timestamp in the chart."),
    ],
))

DOCS.append(doc(
    "POL-PS-106", "policy", "Pressure Injury Prevention Policy", "Chief Nursing Officer",
    "2025-01-25",
    [
        ("2.1", "Risk Screening", "All inpatients are screened for pressure-injury risk using a "
         "validated scale within 8 hours of admission and every 24 hours thereafter."),
        ("2.2", "Repositioning Schedule", "Patients identified as at-risk must be repositioned at "
         "minimum every 2 hours, with the schedule documented on the bedside repositioning chart."),
        ("2.3", "Responsible Role", "The bedside nursing assistant performs repositioning; the "
         "registered nurse verifies skin integrity at each shift change."),
    ],
))

# ---------------------------------------------------------------------------
# 3. Consent procedures (5 documents)
# ---------------------------------------------------------------------------
DOCS.append(doc(
    "SOP-CON-201", "sop", "Informed Consent for Surgical Procedures SOP", "Chief of Surgery",
    "2025-02-05",
    [
        ("2.1", "Elements of Consent", "Informed consent must document the diagnosis, the proposed "
         "procedure, material risks and benefits, reasonable alternatives, and the consequences of "
         "declining treatment."),
        ("2.2", "Timing", "Consent must be obtained by the operating surgeon before any pre-"
         "operative sedation is administered, and no later than the day before an elective "
         "procedure."),
        ("2.3", "Responsible Role", "Only the performing surgeon, or a credentialed delegate who "
         "will be present for the procedure, may obtain surgical consent."),
        ("2.4", "Withdrawal of Consent", "A patient may withdraw consent verbally at any point "
         "before incision; the withdrawal must be documented immediately and the procedure "
         "cancelled or postponed."),
    ],
))

DOCS.append(doc(
    "SOP-CON-202", "sop", "Consent for Minors and Incapacitated Patients SOP",
    "Chief Medical Officer", "2025-02-08",
    [
        ("3.1", "Minors", "For patients under 18, consent must be obtained from a parent or legal "
         "guardian, except in emergency situations under the emergency-treatment exception in "
         "POL-CON-204."),
        ("3.2", "Incapacitated Adults", "When an adult patient lacks decision-making capacity, "
         "consent is obtained from the legally authorized representative in the order established "
         "by facility policy: healthcare proxy, then spouse, then adult child, then parent."),
        ("3.3", "Responsible Role", "The attending physician determines and documents capacity; the "
         "unit social worker assists in identifying the legally authorized representative."),
    ],
))

DOCS.append(doc(
    "SOP-CON-203", "sop", "Consent for Blood Product Transfusion SOP", "Chief Medical Officer",
    "2025-02-12",
    [
        ("2.1", "Separate Consent Requirement", "Transfusion of blood or blood products requires a "
         "separate written consent distinct from general procedural consent, documenting the "
         "specific product, indication, and risk of transfusion reaction."),
        ("2.2", "Responsible Role", "The ordering physician obtains transfusion consent; the "
         "administering nurse verifies the signed consent is present in the chart before hanging "
         "the unit."),
        ("2.3", "Refusal", "A documented refusal of blood products (e.g., on religious grounds) "
         "must trigger a bloodless-medicine care-plan consult per the compliance manual COMP-005 "
         "section 4.3."),
    ],
))

DOCS.append(doc(
    "POL-CON-204", "policy", "Emergency Treatment Exception to Consent Policy",
    "Chief Medical Officer", "2025-02-15",
    [
        ("2.1", "Applicability", "When a patient faces an immediate, life-threatening emergency and "
         "is unable to consent, and no legally authorized representative is immediately available, "
         "treatment necessary to prevent death or serious harm may proceed without prior consent."),
        ("2.2", "Documentation", "The attending physician must document the emergency basis for "
         "proceeding without consent in the chart within 1 hour of the intervention."),
        ("2.3", "Responsible Role", "The attending physician makes and documents the emergency-"
         "exception determination."),
    ],
))

DOCS.append(doc(
    "SOP-CON-205", "sop", "Research Study Consent SOP", "Institutional Review Coordinator",
    "2025-02-18",
    [
        ("2.1", "IRB Approval Prerequisite", "No research consent may be obtained from a patient "
         "until the study has active Institutional Review Board (IRB) approval and the current "
         "consent form version is on file."),
        ("2.2", "Voluntary Participation Statement", "The consent form must explicitly state that "
         "participation is voluntary and that declining will not affect the patient's standard of "
         "care."),
        ("2.3", "Responsible Role", "The principal investigator or a delegated, trained research "
         "coordinator obtains research consent."),
    ],
))

# ---------------------------------------------------------------------------
# 4. Compliance manual (6 documents)
# ---------------------------------------------------------------------------
DOCS.append(doc(
    "COMP-005", "compliance_manual", "Hospital Compliance Manual — Incident Management",
    "Compliance Officer", "2025-01-01",
    [
        ("4.3", "Bloodless-Medicine Consult", "When a patient refuses blood products, the ordering "
         "physician must request a bloodless-medicine consult within 4 hours to establish an "
         "alternative care plan."),
        ("6.1", "Incident Severity Levels", "Incidents are classified Level 1 (no harm) through "
         "Level 4 (sentinel event). Level 3 and Level 4 events require notification to the "
         "Compliance Officer within 1 hour."),
        ("6.2", "Cluster Escalation", "A suspected infection cluster of three or more linked cases "
         "escalates automatically to the Hospital Safety Committee and must be logged within 24 "
         "hours of identification."),
        ("6.3", "Root-Cause Analysis", "All Level 3 and Level 4 incidents require a formal "
         "root-cause analysis completed within 30 calendar days, with corrective actions tracked "
         "to closure."),
    ],
))

DOCS.append(doc(
    "COMP-006", "compliance_manual", "Hospital Compliance Manual — Data Privacy and PHI Handling",
    "Compliance Officer", "2025-01-01",
    [
        ("2.1", "Minimum Necessary Standard", "Staff may access only the protected health "
         "information (PHI) minimally necessary to perform their assigned duties."),
        ("2.2", "Breach Reporting", "A suspected PHI breach must be reported to the Compliance "
         "Officer within 1 hour of discovery. The Compliance Officer determines notification "
         "obligations within 5 working days."),
        ("2.3", "Responsible Role", "Every staff member is individually responsible for reporting a "
         "suspected breach; the Compliance Officer owns the formal breach assessment."),
        ("2.4", "Device Security", "PHI may not be stored on unencrypted portable devices. Any lost "
         "or stolen device suspected to contain PHI must be reported within 1 hour."),
    ],
))

DOCS.append(doc(
    "COMP-007", "compliance_manual", "Hospital Compliance Manual — Controlled Substance Handling",
    "Chief Pharmacy Officer", "2025-01-01",
    [
        ("3.1", "Dual Custody", "Controlled substances must be stored in a locked automated "
         "dispensing cabinet requiring two-factor identification for withdrawal."),
        ("3.2", "Waste Documentation", "Any wasted controlled-substance dose must be witnessed and "
         "co-signed by a second licensed staff member within the same shift."),
        ("3.3", "Discrepancy Escalation", "An unresolved controlled-substance discrepancy must be "
         "escalated to the Chief Pharmacy Officer within 2 hours and to the Compliance Officer "
         "within 24 hours if unresolved."),
        ("3.4", "Responsible Role", "The dispensing nurse and pharmacist share responsibility for "
         "dual-custody verification at each withdrawal."),
    ],
))

DOCS.append(doc(
    "COMP-008", "compliance_manual", "Hospital Compliance Manual — Staff Credentialing and Training",
    "Compliance Officer", "2025-01-01",
    [
        ("2.1", "Initial Credentialing", "Clinical staff may not provide unsupervised patient care "
         "until primary-source verification of license and required competencies is complete."),
        ("2.2", "Annual Competency Review", "All clinical staff must complete annual competency "
         "review for hand hygiene, PPE use, and fall-prevention protocols; non-completion within 30 "
         "days of the due date suspends clinical scheduling privileges."),
        ("2.3", "Responsible Role", "Unit managers verify staff training completion; the Compliance "
         "Officer audits completion rates quarterly."),
    ],
))

DOCS.append(doc(
    "COMP-009", "compliance_manual", "Hospital Compliance Manual — Complaint and Grievance Handling",
    "Patient Relations Manager", "2025-01-01",
    [
        ("2.1", "Complaint Intake", "Any verbal or written patient complaint must be logged in the "
         "grievance system within 24 hours of receipt."),
        ("2.2", "Response Timeline", "A written response addressing the grievance must be sent to "
         "the patient or representative within 7 calendar days, or a written status update if the "
         "investigation is still open."),
        ("2.3", "Responsible Role", "The Patient Relations Manager owns grievance intake and "
         "response; unit managers must provide requested factual information within 3 working "
         "days."),
    ],
))

DOCS.append(doc(
    "COMP-010", "compliance_manual", "Hospital Compliance Manual — External Regulatory Inspection Readiness",
    "Compliance Officer", "2025-01-01",
    [
        ("2.1", "Document Availability", "All policies, SOPs, and training records referenced in "
         "this manual must be retrievable within 15 minutes of a regulator's request during an "
         "on-site inspection."),
        ("2.2", "Designated Liaison", "The Compliance Officer serves as the designated liaison for "
         "all external regulatory inspections and must be notified immediately upon an inspector's "
         "arrival."),
        ("2.3", "Corrective Action Plans", "Any regulatory finding requires a corrective action "
         "plan submitted within 10 working days of the finding being issued."),
    ],
))

# ---------------------------------------------------------------------------
# 5. Operational policies (8 documents)
# ---------------------------------------------------------------------------
DOCS.append(doc(
    "POL-OPS-301", "policy", "Patient Admission and Bed Assignment Policy",
    "Chief Nursing Officer", "2025-02-20",
    [
        ("2.1", "Bed Assignment Priority", "Bed assignment prioritizes clinical acuity first, then "
         "infection-control isolation needs, then length-of-stay optimization."),
        ("2.2", "Responsible Role", "The house supervisor makes final bed-assignment decisions "
         "during off-hours; the admitting charge nurse decides during regular shifts."),
    ],
))

DOCS.append(doc(
    "POL-OPS-302", "policy", "Discharge Planning Policy", "Chief Nursing Officer", "2025-02-22",
    [
        ("2.1", "Discharge Readiness Criteria", "Discharge requires a documented physician order, "
         "medication reconciliation, and confirmation the patient or caregiver can articulate the "
         "discharge instructions."),
        ("2.2", "Responsible Role", "The bedside nurse performs medication reconciliation and "
         "teach-back; the case manager coordinates post-discharge services."),
        ("2.3", "High-Risk Readmission Follow-Up", "Patients flagged high risk for readmission "
         "receive a follow-up phone call from the case manager within 48 hours of discharge."),
    ],
))

DOCS.append(doc(
    "SOP-OPS-303", "sop", "Nurse Staffing Ratio SOP", "Chief Nursing Officer", "2025-02-25",
    [
        ("2.1", "Minimum Ratios", "Minimum nurse-to-patient ratios are 1:4 on general medical-"
         "surgical units and 1:2 in the intensive care unit."),
        ("2.2", "Ratio Breach Escalation", "If a unit falls below the minimum ratio for more than "
         "30 minutes, the charge nurse must notify the house supervisor, who arranges relief "
         "staffing or activates the staffing contingency plan."),
        ("2.3", "Responsible Role", "The charge nurse monitors ratio compliance each shift; the "
         "house supervisor owns escalation."),
    ],
))

DOCS.append(doc(
    "SOP-OPS-304", "sop", "Equipment Maintenance and Calibration SOP", "Biomedical Engineering Manager",
    "2025-03-01",
    [
        ("2.1", "Calibration Interval", "Life-support and infusion equipment must be calibrated at "
         "intervals defined by the manufacturer, and no less frequently than every 12 months."),
        ("2.2", "Out-of-Service Tagging", "Equipment that fails calibration or is suspected faulty "
         "must be tagged out of service immediately and removed from the clinical area within 1 "
         "hour."),
        ("2.3", "Responsible Role", "Biomedical Engineering performs calibration; the unit charge "
         "nurse ensures faulty equipment is not reused before it is tagged."),
    ],
))

DOCS.append(doc(
    "POL-OPS-305", "policy", "Visitor Management Policy", "Chief Operating Officer", "2025-03-03",
    [
        ("2.1", "Standard Visiting Hours", "Standard visiting hours are 08:00 to 20:00. Immediate "
         "family may be present outside these hours for patients in critical condition, subject to "
         "unit-level approval."),
        ("2.2", "Isolation Room Visitors", "Visitors to isolation rooms must don the same PPE "
         "required for staff, as defined in SOP-IC-002, and are limited to two visitors at a time."),
        ("2.3", "Responsible Role", "The unit charge nurse approves visitor exceptions outside "
         "standard hours."),
    ],
))

DOCS.append(doc(
    "SOP-OPS-306", "sop", "Emergency Code Response SOP (Code Blue)", "Chief Medical Officer",
    "2025-03-05",
    [
        ("2.1", "Activation", "Any staff member who identifies cardiac or respiratory arrest must "
         "immediately activate the Code Blue system via the nearest emergency call point or "
         "overhead page."),
        ("2.2", "Response Time Standard", "The designated resuscitation team must arrive at the "
         "bedside within 3 minutes of activation, facility-wide."),
        ("2.3", "Responsible Role", "The first responder begins basic life support immediately; the "
         "resuscitation team leader assumes clinical command on arrival."),
        ("2.4", "Post-Event Debrief", "A structured debrief must occur within 24 hours of every "
         "Code Blue event, documented by the resuscitation team leader."),
    ],
))

DOCS.append(doc(
    "POL-OPS-307", "policy", "Interpreter and Language Access Policy", "Patient Relations Manager",
    "2025-03-08",
    [
        ("2.1", "Qualified Interpreter Requirement", "For any consent discussion or significant "
         "clinical conversation with a patient who has limited English proficiency, a qualified "
         "medical interpreter (in-person or via approved video/phone service) must be used. Family "
         "members may not interpret for consent discussions."),
        ("2.2", "Responsible Role", "The treating clinician requests interpreter services; the unit "
         "clerk arranges access within 15 minutes for urgent situations."),
    ],
))

DOCS.append(doc(
    "SOP-OPS-308", "sop", "Sharps Injury and Exposure Management SOP", "Occupational Health Manager",
    "2025-03-10",
    [
        ("2.1", "Immediate First Aid", "After a sharps injury, the affected staff member must wash "
         "the site with soap and water immediately and report to Occupational Health within 1 "
         "hour."),
        ("2.2", "Source Patient Testing", "With appropriate consent, source-patient bloodborne "
         "pathogen testing must be initiated within 2 hours of the exposure event."),
        ("2.3", "Responsible Role", "The exposed staff member initiates first aid and reporting; "
         "Occupational Health manages post-exposure prophylaxis decisions and follow-up."),
        ("2.4", "Documentation", "The exposure event must be logged as a Level 2 or higher incident "
         "per COMP-005 section 6.1, depending on source status."),
    ],
))

# ---------------------------------------------------------------------------
print(f"Generated {len(DOCS)} synthetic corpus documents in {os.path.abspath(OUT_DIR)}")
assert len(DOCS) >= 30, "Corpus must contain at least 30 documents per AC-01."
