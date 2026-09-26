import fitz # PyMuPDF
import os

def generate_sample_tender_pdf(output_path: str):
    """
    Generates a realistic 3-page GeM Tender PDF document for testing text and layout extraction.
    """
    doc = fitz.open()
    
    # Page 1: Cover & General Information
    page1 = doc.new_page()
    text_page1 = """GOVERNMENT E-MARKETPLACE (GeM)
TENDER SPECIFICATION & BID COMPLIANCE DOCUMENT

Tender Reference: GEM/2026/B/891023
Department: Ministry of Defense - Military Engineer Services
Issue Date: 2026-09-10
Closing Date: 2026-10-30

1. OBJECTIVE & SCOPE OF WORK
The Ministry of Defense invites eligible bids for the turnkey supply, installation, and commissioning of Data Center Infrastructure, High-Performance Servers, and Cyber Security Appliances across 5 regional naval bases.

2. ELIGIBILITY CRITERIA
- The bidder must be an Indian registered entity under the Companies Act, 2013 or LLP Act, 2008.
- Joint ventures (JVs) or consortiums are NOT permitted for this procurement.
- Bidder must possess valid ISO 9001:2015 and ISO 27001:2013 certifications at the time of submission.
"""
    page1.insert_text((50, 50), text_page1, fontsize=11)

    # Page 2: Financial & Technical Requirements
    page2 = doc.new_page()
    text_page2 = """SECTION II: FINANCIAL & TECHNICAL COMPLIANCE REQUIREMENTS

3. FINANCIAL CAPACITY & TURNOVER
- Minimum Annual Turnover: The bidder must have an average annual financial turnover of at least INR 5.00 Crore (Rupees Five Crore Only) during the last 3 financial years (FY 2022-23, FY 2023-24, FY 2024-25).
- Audited Financial Statements: Certified Chartered Accountant (CA) certificates with UDIN must be uploaded.
- Earnest Money Deposit (EMD): EMD of INR 10,00,000/- (Rupees Ten Lakhs Only) via Bank Guarantee or online GeM transfer.

4. TECHNICAL CAPACITY & EXPERIENCE
- Past Performance: Bidder must have successfully executed at least 3 similar contracts for Central/State Govt departments with minimum order value of INR 2.00 Crore each in the last 5 years.
- Local OEM Authorization: MAF (Manufacturer Authorization Form) required for all server and firewall hardware.
"""
    page2.insert_text((50, 50), text_page2, fontsize=11)

    # Page 3: Mandatory Documents List
    page3 = doc.new_page()
    text_page3 = """SECTION III: MANDATORY DOCUMENTS CHECKLIST

The following documents MUST be attached in the technical bid packet:
1. Certificate of Incorporation & GST Registration Certificate.
2. Audited Balance Sheets for FY 2022-23, 2023-24, and 2024-25.
3. CA Certified Turnover Certificate with UDIN.
4. ISO 9001:2015 & ISO 27001 Certificates.
5. OEM Authorization Letter (MAF) from original equipment manufacturer.
6. Undertaking on non-blacklisting by any Govt entity on Rs. 100 non-judicial stamp paper.

Failure to submit any mandatory document will result in instant technical disqualification.
"""
    page3.insert_text((50, 50), text_page3, fontsize=11)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()
    print(f"Generated sample tender PDF at: {output_path}")

if __name__ == "__main__":
    generate_sample_tender_pdf("./data/sample_tenders/sample_gem_tender.pdf")
