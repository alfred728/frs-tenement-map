#!/usr/bin/env python3
"""
Add professional landing page with email gate to FRS Timeline Map.
- MST Financial + Forrestania Resources dual branding
- Email, Name, Company collection
- localStorage gating with Airtable-ready template
"""

MAP_FILE = '/Users/alfredlewis/Documents/Forrestania Resources/frs_tenement_timeline_map.html'

with open(MAP_FILE, 'r') as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════
# 1. Fix stray HTML entity dashes (lines 274-275)
# ═══════════════════════════════════════════════════════════
content = content.replace(
    '<div class="date" id="card-date">&ndash;</div>',
    '<div class="date" id="card-date">-</div>'
)
content = content.replace(
    'Forrestania Resources &mdash; Starting Position',
    'Forrestania Resources - Starting Position'
)
print("Fixed HTML entity dashes")

# ═══════════════════════════════════════════════════════════
# 2. Insert landing page CSS before </style>
# ═══════════════════════════════════════════════════════════
LANDING_CSS = """
/* ── Landing page / email gate ── */
#landing-page{position:fixed;top:0;left:0;right:0;bottom:0;z-index:9999;background:linear-gradient(135deg,#0d1117 0%,#161b22 40%,#1c2333 100%);display:flex;align-items:center;justify-content:center;transition:opacity 0.6s ease;overflow-y:auto}
#landing-page.fade-out{opacity:0;pointer-events:none}
.lp-card{width:100%;max-width:640px;margin:40px 20px;padding:48px 44px 36px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:16px;backdrop-filter:blur(20px);box-shadow:0 24px 80px rgba(0,0,0,0.4)}
.lp-logos{display:flex;align-items:center;justify-content:center;gap:24px;margin-bottom:32px}
.lp-logos .lp-divider{width:1px;height:32px;background:rgba(255,255,255,0.2)}
.lp-logos img{height:32px;object-fit:contain}
.lp-logos svg{height:28px;width:auto}
.lp-title{font-size:22px;font-weight:700;color:#ffffff;text-align:center;margin-bottom:6px;line-height:1.3}
.lp-subtitle{font-size:13px;color:rgba(255,255,255,0.5);text-align:center;margin-bottom:28px;letter-spacing:0.5px;text-transform:uppercase}
.lp-intro{font-size:14px;color:rgba(255,255,255,0.75);line-height:1.7;margin-bottom:24px;text-align:left}
.lp-intro p{margin-bottom:12px}
.lp-disclaimer{font-size:10.5px;color:rgba(255,255,255,0.35);line-height:1.6;margin-bottom:28px;padding:14px 16px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:8px}
.lp-disclaimer a{color:rgba(255,255,255,0.5);text-decoration:underline}
.lp-form{display:flex;flex-direction:column;gap:12px;margin-bottom:20px}
.lp-field{display:flex;flex-direction:column;gap:4px}
.lp-field label{font-size:11px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:0.8px;font-weight:600}
.lp-field input{padding:10px 14px;border:1px solid rgba(255,255,255,0.12);border-radius:8px;background:rgba(255,255,255,0.06);color:#ffffff;font-size:14px;font-family:inherit;outline:none;transition:border-color 0.2s}
.lp-field input:focus{border-color:rgba(255,255,255,0.3)}
.lp-field input::placeholder{color:rgba(255,255,255,0.25)}
.lp-field input.lp-error{border-color:#f85149}
.lp-error-msg{font-size:11px;color:#f85149;margin-top:-6px;margin-bottom:4px;display:none}
.lp-submit{padding:12px 24px;border:none;border-radius:8px;background:linear-gradient(135deg,#238636,#2ea043);color:#ffffff;font-size:15px;font-weight:600;font-family:inherit;cursor:pointer;transition:transform 0.15s,box-shadow 0.15s;letter-spacing:0.3px;margin-top:4px}
.lp-submit:hover{transform:translateY(-1px);box-shadow:0 4px 16px rgba(35,134,54,0.4)}
.lp-submit:active{transform:translateY(0)}
.lp-footer{text-align:center;font-size:11px;color:rgba(255,255,255,0.25);margin-top:8px}
"""

content = content.replace('</style>', LANDING_CSS + '</style>')
print("Inserted landing page CSS")

# ═══════════════════════════════════════════════════════════
# 3. Insert landing page HTML after <body>
# ═══════════════════════════════════════════════════════════
LANDING_HTML = """<div id="landing-page">
  <div class="lp-card">
    <div class="lp-logos">
      <svg width="204" height="28" viewBox="0 0 204 28" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M4.95982 22.7333V24.7071H0V17.7048L4.95982 22.7333Z" fill="white"/><path d="M16.9325 11.6523V24.7069H11.9727V16.6808L16.9325 11.6523Z" fill="white"/><path d="M22.9197 5.58301V24.707H17.957V10.6114L22.9197 5.58301Z" fill="white"/><path d="M22.9197 0V4.10978L17.957 9.14106V5.02844L22.9197 0Z" fill="white"/><path d="M50.2706 24.6672H47.3447V11.7918L41.9248 20.8731H41.568L36.1486 11.7662V24.6672H33.2227V6.60693H36.3786L41.748 15.6371L47.1427 6.60693H50.2734V24.6672H50.2706Z" fill="white"/><path d="M52.6367 20.5632L55.1559 19.0672C55.7927 20.8988 57.1673 22.1104 59.5827 22.1104C62.0012 22.1104 62.8902 21.0524 62.8902 19.7355C62.8902 18.1371 61.4903 17.5939 58.8449 16.7691C56.0704 15.9187 53.3745 14.8863 53.3745 11.479C53.3745 8.07174 56.0985 6.26855 59.1002 6.26855C62.1019 6.26855 64.189 7.84136 65.3084 10.2418L62.8397 11.6866C62.2029 10.2418 61.0836 9.158 59.1002 9.158C57.3974 9.158 56.4549 9.98123 56.4549 11.2726C56.4549 12.6918 57.5489 13.2606 60.2448 14.1366C63.2465 15.1178 65.9705 16.0962 65.9705 19.5547C65.9705 22.9364 63.5551 24.9984 59.5322 24.9984C56.0452 24.9984 53.7283 23.2436 52.6367 20.5632Z" fill="white"/><path d="M76.0215 9.69596H69.9766V6.60693H85.1463V9.69596H79.1014V24.6672H76.0215V9.69596Z" fill="white"/><path d="M103.692 6.60693V24.6672H100.612V16.8459H91.8005V24.6672H88.7207V6.60693H91.8005V13.757H100.612V6.60693H103.692Z" fill="white"/><path d="M108.105 6.60693H111.185V13.757H118.634V6.60693H121.714V24.6672H118.634V16.8459H111.185V24.6672H108.105V6.60693Z" fill="white"/><path d="M126.047 6.60693H129.127V13.4418L136.091 6.60693H140.114L132.41 13.9546L140.471 24.6672H136.524L130.301 16.3578L129.127 17.5174V24.6672H126.047V6.60693Z" fill="white"/><path d="M148.852 6.26855C154.386 6.26855 158.843 10.3698 158.843 15.637C158.843 20.9042 154.386 24.9984 148.852 24.9984C143.322 24.9984 138.891 20.9042 138.891 15.637C138.891 10.3698 143.326 6.26855 148.852 6.26855ZM148.852 21.9614C152.515 21.9614 155.613 19.3066 155.613 15.637C155.613 11.9674 152.515 9.30824 148.852 9.30824C145.192 9.30824 142.121 11.9674 142.121 15.637C142.121 19.3066 145.192 21.9614 148.852 21.9614Z" fill="white"/><path d="M161.492 6.60693H167.537C172.207 6.60693 175.362 9.69596 175.362 13.4418C175.362 17.2134 172.207 20.2768 167.537 20.2768H164.572V24.6672H161.492V6.60693ZM167.235 17.1878C170.314 17.1878 172.132 15.637 172.132 13.4418C172.132 11.2466 170.314 9.69596 167.235 9.69596H164.572V17.1878H167.235Z" fill="white"/><path d="M178.248 6.60693H187.668C190.697 6.60693 192.398 8.36132 192.398 10.7106C192.398 12.4394 191.535 13.7826 190.085 14.3514C191.868 14.869 193.086 16.4954 193.086 18.4038C193.086 21.0842 191.182 24.6672 186.284 24.6672H178.248V6.60693ZM186.539 13.5186C188.497 13.5186 189.414 12.4862 189.414 11.0926C189.414 9.699 188.446 9.36332 186.539 9.36332H181.328V13.5186H186.539ZM186.793 21.9102C189.156 21.9102 190.102 20.4142 190.102 18.6342C190.102 17.0358 189.003 15.7446 186.843 15.7446H181.328V21.9102H186.793Z" fill="white"/><path d="M203.997 24.6672H196.445V6.60693H203.997C204.016 6.60693 204.016 9.54316 204.016 9.54316H199.524V13.757H203.317V16.8459H199.524V21.7782H203.997V24.6672Z" fill="white"/></svg>
      <div class="lp-divider"></div>
      <img src="https://images.squarespace-cdn.com/content/v1/6098839bb96d655ec6ab0524/454d48c7-9588-4916-9507-07cb13160350/logo_Forrestania-Resources.png" alt="Forrestania Resources" style="height:36px">
    </div>
    <div class="lp-title">Forrestania Resources (ASX: FRS)</div>
    <div class="lp-subtitle">Strategic Acquisition Timeline & Scenario Analysis</div>
    <div class="lp-intro">
      <p>This interactive tool maps the strategic transformation of Forrestania Resources from a single-project explorer into one of Western Australia's fastest-growing gold consolidators.</p>
      <p>Explore 35 acquisitions across the Forrestania, Westonia, Coolgardie and Eastern Goldfields hubs, track over 600,000 ounces of JORC gold resources assembled in under 12 months, and examine the path to production at the Lake Johnston processing plant - targeted at up to 100,000 ounces per annum by end of 2026.</p>
      <p>Navigate the timeline event-by-event or use the controls to view the full picture, compare nearby regional resources, and assess the portfolio's strategic positioning.</p>
    </div>
    <div class="lp-disclaimer">
      All material in this tool has been prepared by MST Financial Services Pty Limited (ABN 54 617 475 180, AFSL 500 557) for general informational purposes only and is not a solicitation of any offer to buy or sell any financial instrument or to participate in any trading strategy. This material is not a research report as defined under ASIC guidance. For wholesale clients only. This material is only prepared for wholesale clients pursuant to section 761G(7) of the Corporations Act (Commonwealth). Please also refer to MST's <a href="https://mstfinancial.com.au/privacy-policy" target="_blank">Privacy Policy</a>, <a href="https://mstfinancial.com.au/terms-of-use" target="_blank">Terms of Use</a> and <a href="https://mstfinancial.com.au/financial-services-guide" target="_blank">Financial Services Guide</a>.
    </div>
    <form class="lp-form" id="lp-form" onsubmit="return false">
      <div class="lp-field">
        <label for="lp-email">Email address</label>
        <input type="email" id="lp-email" placeholder="you@company.com" required autocomplete="email">
      </div>
      <div id="lp-email-error" class="lp-error-msg">Please enter a valid email address</div>
      <div class="lp-field">
        <label for="lp-name">Full name</label>
        <input type="text" id="lp-name" placeholder="Jane Smith" required autocomplete="name">
      </div>
      <div id="lp-name-error" class="lp-error-msg">Please enter your name</div>
      <div class="lp-field">
        <label for="lp-company">Company</label>
        <input type="text" id="lp-company" placeholder="Company Pty Ltd" required autocomplete="organization">
      </div>
      <div id="lp-company-error" class="lp-error-msg">Please enter your company name</div>
      <button type="submit" class="lp-submit" id="lp-submit">Access Map</button>
    </form>
    <div class="lp-footer">&copy; 2026 MST Financial Services Pty Limited. All rights reserved.</div>
  </div>
</div>
"""

content = content.replace('<body>\n', '<body>\n' + LANDING_HTML)
print("Inserted landing page HTML")

# ═══════════════════════════════════════════════════════════
# 4. Insert landing page JS after <script>
# ═══════════════════════════════════════════════════════════
LANDING_JS = """
// ── Landing page gate ──
(function() {
  var LP_KEY = 'frs_map_access';
  var landing = document.getElementById('landing-page');

  // Check if user already registered
  var stored = null;
  try { stored = JSON.parse(localStorage.getItem(LP_KEY)); } catch(e) {}

  if (stored && stored.email) {
    // Returning visitor - hide landing immediately
    landing.style.display = 'none';
    return;
  }

  // New visitor - show landing page
  var form = document.getElementById('lp-form');
  var emailInput = document.getElementById('lp-email');
  var nameInput = document.getElementById('lp-name');
  var companyInput = document.getElementById('lp-company');
  var submitBtn = document.getElementById('lp-submit');

  function showError(id, show) {
    var el = document.getElementById(id);
    el.style.display = show ? 'block' : 'none';
    return !show;
  }

  function validateEmail(email) {
    return /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(email);
  }

  submitBtn.addEventListener('click', function() {
    var email = emailInput.value.trim();
    var name = nameInput.value.trim();
    var company = companyInput.value.trim();

    // Reset errors
    emailInput.classList.remove('lp-error');
    nameInput.classList.remove('lp-error');
    companyInput.classList.remove('lp-error');

    var valid = true;

    if (!validateEmail(email)) {
      emailInput.classList.add('lp-error');
      valid = showError('lp-email-error', true) && valid;
      valid = false;
    } else {
      showError('lp-email-error', false);
    }

    if (!name) {
      nameInput.classList.add('lp-error');
      valid = showError('lp-name-error', true) && valid;
      valid = false;
    } else {
      showError('lp-name-error', false);
    }

    if (!company) {
      companyInput.classList.add('lp-error');
      valid = showError('lp-company-error', true) && valid;
      valid = false;
    } else {
      showError('lp-company-error', false);
    }

    if (!valid) return;

    // Store locally
    var record = {
      email: email,
      name: name,
      company: company,
      timestamp: new Date().toISOString()
    };
    localStorage.setItem(LP_KEY, JSON.stringify(record));

    // AIRTABLE INTEGRATION (uncomment and add your PAT to enable)
    // var AIRTABLE_PAT = 'YOUR_PERSONAL_ACCESS_TOKEN';
    // var AIRTABLE_BASE = 'appMRp6SDOS9kvdDy';
    // var AIRTABLE_TABLE = 'FRS Map Access';
    // fetch('https://api.airtable.com/v0/' + AIRTABLE_BASE + '/' + encodeURIComponent(AIRTABLE_TABLE), {
    //   method: 'POST',
    //   headers: {
    //     'Authorization': 'Bearer ' + AIRTABLE_PAT,
    //     'Content-Type': 'application/json'
    //   },
    //   body: JSON.stringify({ fields: { Email: email, Name: name, Company: company, 'Accessed At': record.timestamp } })
    // }).catch(function(err) { console.warn('Airtable sync failed:', err); });

    // Fade out landing page
    landing.classList.add('fade-out');
    setTimeout(function() {
      landing.style.display = 'none';
    }, 650);
  });

  // Allow Enter key to submit
  form.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      submitBtn.click();
    }
  });
})();

"""

content = content.replace('<script>\n', '<script>\n' + LANDING_JS)
print("Inserted landing page JavaScript")

# ═══════════════════════════════════════════════════════════
# Write output
# ═══════════════════════════════════════════════════════════
with open(MAP_FILE, 'w') as f:
    f.write(content)

print("\nDone. Landing page added to FRS timeline map.")
