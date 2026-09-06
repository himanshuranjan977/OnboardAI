import React, {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { createRoot } from "react-dom/client";
import "./styles.css";

/* =========================================================
   API CONFIGURATION
========================================================= */

const API = (
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000"
).replace(/\/+$/, "");

/* =========================================================
   STATUS MAP
========================================================= */

const statusMap = {
  APPROVED: ["Approved", "green"],
  REJECTED: ["Rejected", "red"],
  HUMAN_REVIEW: ["Human review", "amber"],
  WAITING_FOR_HUMAN_REVIEW: ["Human review", "amber"],
  IN_PROGRESS: ["In progress", "blue"],
  DOCUMENT_COLLECTION: ["Documents", "purple"],
  COMPLETED: ["Completed", "green"],
  CREATED: ["Created", "slate"],
  PROCESSING: ["Processing", "blue"],
  VERIFIED: ["Verified", "green"],
  REQUIRES_REVIEW: ["Review", "amber"],
  PENDING: ["Pending", "amber"],
  FAILED: ["Failed", "red"],
  QUEUED: ["Queued", "amber"],
  RUNNING: ["Running", "blue"],
};

/* =========================================================
   SAFE API HELPER
========================================================= */

async function api(path, options = {}) {
  const token = localStorage.getItem("onboardai_token");

  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  /*
   * Only set Content-Type automatically when a body exists
   * and the caller did not already provide one.
   *
   * This is important for FormData uploads.
   */
  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has("Content-Type")
  ) {
    headers.set("Content-Type", "application/json");
  }

  let response;

  try {
    response = await fetch(`${API}${path}`, {
      ...options,
      headers,
    });
  } catch (error) {
    throw new Error(
      `Unable to connect to OnboardAI API. Please check the backend at ${API}.`
    );
  }

  const text = await response.text();

  let data = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;

    if (typeof data === "string" && data.trim()) {
      message = data;
    } else if (data?.detail) {
      if (Array.isArray(data.detail)) {
        message = data.detail
          .map((item) => {
            if (typeof item === "string") return item;

            const location = Array.isArray(item?.loc)
              ? item.loc.join(" → ")
              : "";

            return location
              ? `${location}: ${item.msg || "Validation error"}`
              : item?.msg || "Validation error";
          })
          .join("\n");
      } else {
        message = String(data.detail);
      }
    } else if (data?.message) {
      message = String(data.message);
    } else if (data?.error) {
      message = String(data.error);
    }

    throw new Error(message);
  }

  return data;
}

/* =========================================================
   DOCUMENT VIEWER
========================================================= */

async function openOriginalDocument(documentId) {
  const token = localStorage.getItem("onboardai_token");

  let response;

  try {
    response = await fetch(
      `${API}/api/documents/${documentId}/file`,
      {
        headers: token
          ? {
              Authorization: `Bearer ${token}`,
            }
          : {},
      }
    );
  } catch {
    throw new Error(
      "Unable to connect to the backend while opening the document."
    );
  }

  if (!response.ok) {
    let message = "Unable to open document.";

    try {
      const data = await response.json();

      if (Array.isArray(data?.detail)) {
        message = data.detail
          .map((item) => item?.msg || String(item))
          .join(", ");
      } else if (data?.detail) {
        message = data.detail;
      }
    } catch {
      // Ignore invalid error JSON.
    }

    throw new Error(message);
  }

  const blob = await response.blob();

  const url = URL.createObjectURL(blob);

  const popup = window.open(
    url,
    "_blank",
    "noopener,noreferrer"
  );

  if (!popup) {
    URL.revokeObjectURL(url);
    throw new Error(
      "The browser blocked the document window. Please allow pop-ups for this site."
    );
  }

  setTimeout(() => {
    URL.revokeObjectURL(url);
  }, 60000);
}

/* =========================================================
   HELPERS
========================================================= */

function Badge({ value }) {
  const [label, tone] =
    statusMap[value] || [
      String(value || "")
        .replaceAll("_", " "),
      "slate",
    ];

  return (
    <span className={`badge ${tone}`}>
      {label}
    </span>
  );
}

function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatDateTime(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function pretty(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) =>
      character.toUpperCase()
    );
}

function initials(name) {
  const value = String(name || "U").trim();

  if (!value) return "U";

  return value
    .split(/\s+/)
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

/* =========================================================
   ICON
========================================================= */

function Icon({ name, size = 18 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.8,
    strokeLinecap: "round",
    strokeLinejoin: "round",
  };

  const paths = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" />
        <rect x="14" y="3" width="7" height="7" />
        <rect x="3" y="14" width="7" height="7" />
        <rect x="14" y="14" width="7" height="7" />
      </>
    ),

    users: (
      <>
        <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </>
    ),

    folder: (
      <path d="M3 7.5A2.5 2.5 0 0 1 5.5 5H10l2 2h6.5A2.5 2.5 0 0 1 21 9.5v8A2.5 2.5 0 0 1 18.5 20h-13A2.5 2.5 0 0 1 3 17.5z" />
    ),

    shield: (
      <>
        <path d="M12 3l8 3v5c0 5.2-3.4 8.7-8 10-4.6-1.3-8-4.8-8-10V6z" />
        <path d="m8.5 12 2.2 2.2 4.8-5" />
      </>
    ),

    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),

    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-4-4" />
      </>
    ),

    plus: (
      <path d="M12 5v14M5 12h14" />
    ),

    upload: (
      <>
        <path d="M12 16V4" />
        <path d="m7 9 5-5 5 5" />
        <path d="M5 20h14" />
      </>
    ),

    arrow: (
      <>
        <path d="M5 12h14" />
        <path d="m13 6 6 6-6 6" />
      </>
    ),

    back: (
      <>
        <path d="M19 12H5" />
        <path d="m11 18-6-6 6-6" />
      </>
    ),

    refresh: (
      <>
        <path d="M20 11a8 8 0 0 0-14.9-3L3 11" />
        <path d="M3 5v6h6" />
        <path d="M4 13a8 8 0 0 0 14.9 3L21 13" />
        <path d="M21 19v-6h-6" />
      </>
    ),

    check: (
      <path d="m5 12 4 4L19 6" />
    ),

    x: (
      <path d="m6 6 12 12M18 6 6 18" />
    ),

    file: (
      <>
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <path d="M14 2v6h6" />
      </>
    ),

    activity: (
      <path d="M3 12h4l3-8 4 16 3-8h4" />
    ),

    user: (
      <>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 21a8 8 0 0 1 16 0" />
      </>
    ),

    chevron: (
      <path d="m9 18 6-6-6-6" />
    ),
  };

  return (
    <svg {...common}>
      {paths[name]}
    </svg>
  );
}

/* =========================================================
   LAYOUT
========================================================= */

function Layout({
  page,
  setPage,
  children,
  user,
  onLogout,
}) {
  const staff =
    user &&
    ["ADMIN", "ANALYST", "QA"].includes(
      user.role
    );

  const nav = [
    ["overview", "Overview", "grid"],

    [
      "cases",
      user?.role === "CUSTOMER"
        ? "My KYC Cases"
        : "KYC Cases",
      "folder",
    ],

    [
      "customers",
      user?.role === "CUSTOMER"
        ? "My Profile"
        : "Customers",
      "users",
    ],

    ...(staff
      ? [
          [
            "reviews",
            "Human Review",
            "shield",
          ],
          [
            "monitor",
            "Agent Monitoring",
            "activity",
          ],
        ]
      : []),

    ...(user?.role === "ADMIN"
      ? [
          [
            "users",
            "User Management",
            "users",
          ],
          [
            "emails",
            "Email Notifications",
            "activity",
          ],
        ]
      : []),
  ];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">O</div>

          <div>
            <strong>OnboardAI</strong>
            <span>KYC Operations</span>
          </div>
        </div>

        <div className="nav-label">
          WORKSPACE
        </div>

        <nav>
          {nav.map(([id, label, icon]) => (
            <button
              key={id}
              type="button"
              className={`nav-item ${
                page === id ? "active" : ""
              }`}
              onClick={() => setPage(id)}
            >
              <Icon name={icon} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <div className="system-card">
            <span className="dot"></span>

            <div>
              <b>System healthy</b>
              <small>API connected</small>
            </div>
          </div>

          <div className="profile">
            <div className="avatar">
              {initials(
                user?.full_name ||
                  user?.username
              )}
            </div>

            <div className="grow">
              <b>
                {user?.full_name ||
                  user?.username ||
                  "User"}
              </b>

              <small>
                {user?.role || "USER"}
              </small>
            </div>

            <button
              type="button"
              className="link-btn"
              onClick={onLogout}
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="breadcrumbs">
            Operations <span>/</span>{" "}
            <b>
              {nav.find(
                (item) => item[0] === page
              )?.[1] || "Case"}
            </b>
          </div>

          <div className="top-actions">
            <div className="api-pill">
              <span className="dot"></span>
              Live API
            </div>
          </div>
        </header>

        <div className="content">
          {children}
        </div>
      </main>
    </div>
  );
}

/* =========================================================
   STAT CARD
========================================================= */

function StatCard({
  label,
  value,
  hint,
  icon,
}) {
  return (
    <div className="stat-card">
      <div className="stat-icon">
        <Icon name={icon} />
      </div>

      <div>
        <div className="stat-label">
          {label}
        </div>

        <div className="stat-value">
          {value}
        </div>

        <div className="stat-hint">
          {hint}
        </div>
      </div>
    </div>
  );
}

/* =========================================================
   OVERVIEW
========================================================= */

function Overview({
  setPage,
  openCase,
  user,
}) {
  const [cases, setCases] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);

    try {
      const caseData = await api("/api/cases");

      setCases(
        Array.isArray(caseData)
          ? caseData
          : []
      );

      if (user?.role !== "CUSTOMER") {
        const reviewData =
          await api("/api/reviews/pending");

        setReviews(
          Array.isArray(reviewData)
            ? reviewData
            : []
        );
      } else {
        setReviews([]);
      }
    } catch (error) {
      console.error(
        "Overview loading error:",
        error
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [user?.role]);

  const runCase = async (id) => {
    try {
      const docs = await api(
        `/api/documents/case/${id}`
      );

      if (!Array.isArray(docs) || !docs.length) {
        alert(
          "Upload a PDF document before running KYC agents."
        );
        return;
      }

      await api(
        `/api/workflow/cases/${id}/run`,
        {
          method: "POST",
          body: JSON.stringify({
            document_id: docs[0].id,
          }),
        }
      );

      await refresh();

      openCase(id);
    } catch (error) {
      alert(
        error.message ||
          "Unable to run KYC workflow."
      );
    }
  };

  const approved = cases.filter(
    (item) => item.status === "APPROVED"
  ).length;

  const rejected = cases.filter(
    (item) => item.status === "REJECTED"
  ).length;

  const inReview = cases.filter(
    (item) =>
      [
        "HUMAN_REVIEW",
        "WAITING_FOR_HUMAN_REVIEW",
      ].includes(item.status)
  ).length;

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="eyebrow">
            COMMAND CENTER
          </div>

          <h1>KYC overview</h1>

          <p>
            Monitor onboarding, risk decisions
            and human-review queues.
          </p>
        </div>

        <button
          type="button"
          className="btn secondary"
          onClick={refresh}
        >
          <Icon name="refresh" />
          Refresh
        </button>
      </div>

      <div className="stats-grid">
        <StatCard
          label="Total cases"
          value={
            loading ? "—" : cases.length
          }
          hint="All onboarding cases"
          icon="folder"
        />

        <StatCard
          label="Approved"
          value={
            loading ? "—" : approved
          }
          hint="Final positive decisions"
          icon="check"
        />

        <StatCard
          label="Human review"
          value={
            loading
              ? "—"
              : reviews.length || inReview
          }
          hint="Needs reviewer attention"
          icon="shield"
        />

        <StatCard
          label="Rejected"
          value={
            loading ? "—" : rejected
          }
          hint="Final negative decisions"
          icon="x"
        />
      </div>

      <div className="section-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>Recent cases</h2>
              <span>
                Latest onboarding activity
              </span>
            </div>

            <button
              type="button"
              className="link-btn"
              onClick={() => setPage("cases")}
            >
              View all{" "}
              <Icon name="arrow" size={15} />
            </button>
          </div>

          <CaseTable
            cases={cases.slice(0, 6)}
            onOpen={openCase}
            onRun={
              user?.role === "CUSTOMER"
                ? null
                : runCase
            }
          />
        </div>

        <div className="panel review-panel">
          <div className="panel-head">
            <div>
              <h2>Review queue</h2>
              <span>
                Cases requiring a human decision
              </span>
            </div>

            <span className="count-pill">
              {reviews.length}
            </span>
          </div>

          {reviews.length === 0 ? (
            <Empty text="No pending reviews" />
          ) : (
            reviews
              .slice(0, 5)
              .map((review) => (
                <div
                  className="review-row"
                  key={review.id}
                  onClick={() =>
                    openCase(review.case_id)
                  }
                >
                  <div className="review-icon">
                    <Icon name="shield" />
                  </div>

                  <div className="grow">
                    <b>
                      Review #{review.id}
                    </b>

                    <small>
                      Case #{review.case_id} ·{" "}
                      {review.created_at ||
                        "Pending"}
                    </small>
                  </div>

                  <Icon
                    name="chevron"
                    size={17}
                  />
                </div>
              ))
          )}
        </div>
      </div>
    </section>
  );
}

/* =========================================================
   CASE TABLE
========================================================= */

function CaseTable({
  cases,
  onOpen,
  onRun,
}) {
  if (!cases.length) {
    return (
      <Empty text="No cases found" />
    );
  }

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Case</th>
            <th>Status</th>
            <th>Risk</th>
            <th>Decision</th>
            <th>Updated</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>
          {cases.map((item) => (
            <tr
              key={item.id}
              onClick={() =>
                onOpen(item.id)
              }
            >
              <td>
                <b>
                  {item.case_number ||
                    `CASE-${item.id}`}
                </b>

                <small>
                  ID {item.id}
                </small>
              </td>

              <td>
                <Badge
                  value={item.status}
                />
              </td>

              <td>
                {item.risk_level ? (
                  <span
                    className={`risk ${String(
                      item.risk_level
                    ).toLowerCase()}`}
                  >
                    {item.risk_level}

                    {item.risk_score != null
                      ? ` · ${item.risk_score}`
                      : ""}
                  </span>
                ) : (
                  "—"
                )}
              </td>

              <td>
                {item.decision || "—"}
              </td>

              <td>
                {formatDate(item.updated_at)}
              </td>

              <td>
                <button
                  type="button"
                  className="run-table-btn"
                  onClick={(event) => {
                    event.stopPropagation();

                    if (onRun) {
                      onRun(item.id);
                    }
                  }}
                  disabled={!onRun}
                >
                  ▶ Run KYC
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* =========================================================
   CASES
========================================================= */

function Cases({
  openCase,
  user,
}) {
  const [cases, setCases] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);

    try {
      const data = await api("/api/cases");

      setCases(
        Array.isArray(data) ? data : []
      );
    } catch (error) {
      console.error(
        "Cases loading error:",
        error
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const runCase = async (id) => {
    try {
      const docs = await api(
        `/api/documents/case/${id}`
      );

      if (!Array.isArray(docs) || !docs.length) {
        alert(
          "Upload a PDF document before running KYC agents."
        );
        return;
      }

      await api(
        `/api/workflow/cases/${id}/run`,
        {
          method: "POST",
          body: JSON.stringify({
            document_id: docs[0].id,
          }),
        }
      );

      await load();

      openCase(id);
    } catch (error) {
      alert(
        error.message ||
          "Unable to run KYC workflow."
      );
    }
  };

  const filtered = useMemo(() => {
    const normalizedQuery =
      query.trim().toLowerCase();

    if (!normalizedQuery) {
      return cases;
    }

    return cases.filter((item) =>
      JSON.stringify(item)
        .toLowerCase()
        .includes(normalizedQuery)
    );
  }, [cases, query]);

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="eyebrow">
            ONBOARDING
          </div>

          <h1>KYC cases</h1>

          <p>
            Track every onboarding case from
            document collection to final decision.
          </p>
        </div>

        <button
          type="button"
          className="btn secondary"
          onClick={load}
        >
          <Icon name="refresh" />
          Refresh
        </button>
      </div>

      <div className="panel">
        <div className="toolbar">
          <div className="search">
            <Icon
              name="search"
              size={17}
            />

            <input
              placeholder="Search cases, status, risk..."
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }
            />
          </div>

          <span className="muted">
            {filtered.length} cases
          </span>
        </div>

        {loading ? (
          <Loading />
        ) : (
          <CaseTable
            cases={filtered}
            onOpen={openCase}
            onRun={
              user?.role === "CUSTOMER"
                ? null
                : runCase
            }
          />
        )}
      </div>
    </section>
  );
}

/* =========================================================
   CUSTOMERS
========================================================= */

function Customers({
  setPage,
}) {
  const [customers, setCustomers] =
    useState([]);

  const [show, setShow] =
    useState(false);

  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    date_of_birth: "",
    address: "",
  });

  const [busy, setBusy] =
    useState(false);

  const load = async () => {
    try {
      const data = await api(
        "/api/customers"
      );

      setCustomers(
        Array.isArray(data) ? data : []
      );
    } catch (error) {
      console.error(
        "Customer loading error:",
        error
      );
    }
  };

  useEffect(() => {
    load();
  }, []);

  const resetForm = () => {
    setForm({
      name: "",
      email: "",
      phone: "",
      date_of_birth: "",
      address: "",
    });
  };

  const create = async (event) => {
    event.preventDefault();

    setBusy(true);

    try {
      await api("/api/customers", {
        method: "POST",
        body: JSON.stringify(form),
      });

      resetForm();
      setShow(false);

      await load();
    } catch (error) {
      alert(
        error.message ||
          "Unable to create customer."
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="eyebrow">
            CUSTOMER DIRECTORY
          </div>

          <h1>Customers</h1>

          <p>
            Create customers and start KYC cases
            from the same workspace.
          </p>
        </div>

        <button
          type="button"
          className="btn primary"
          onClick={() => setShow(true)}
        >
          <Icon name="plus" />
          New customer
        </button>
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <h2>Customer directory</h2>

            <span>
              {customers.length} registered
              customers
            </span>
          </div>
        </div>

        {!customers.length ? (
          <Empty text="No customers yet" />
        ) : (
          <div className="customer-grid">
            {customers.map((customer) => (
              <div
                className="customer-card"
                key={customer.id}
              >
                <div className="customer-top">
                  <div className="avatar large">
                    {initials(customer.name)}
                  </div>

                  <div className="grow">
                    <b>{customer.name}</b>
                    <small>
                      {customer.email}
                    </small>
                  </div>
                </div>

                <div className="customer-meta">
                  <span>
                    {customer.phone ||
                      "No phone"}
                  </span>

                  <span>
                    {customer.date_of_birth ||
                      "DOB not set"}
                  </span>
                </div>

                <button
                  type="button"
                  className="btn small"
                  onClick={async () => {
                    try {
                      const created =
                        await api(
                          "/api/cases",
                          {
                            method: "POST",
                            body: JSON.stringify({
                              customer_id:
                                customer.id,
                            }),
                          }
                        );

                      setPage("cases");

                      window.__openCase =
                        created?.id;
                    } catch (error) {
                      alert(
                        error.message ||
                          "Unable to create KYC case."
                      );
                    }
                  }}
                >
                  Start KYC case{" "}
                  <Icon
                    name="arrow"
                    size={14}
                  />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {show && (
        <Modal
          title="Create customer"
          onClose={() => setShow(false)}
        >
          <form
            onSubmit={create}
            className="form"
          >
            <Field
              label="Full name"
              required
              value={form.name}
              onChange={(value) =>
                setForm({
                  ...form,
                  name: value,
                })
              }
            />

            <Field
              label="Email"
              type="email"
              required
              value={form.email}
              onChange={(value) =>
                setForm({
                  ...form,
                  email: value,
                })
              }
            />

            <div className="form-row">
              <Field
                label="Phone"
                value={form.phone}
                onChange={(value) =>
                  setForm({
                    ...form,
                    phone: value,
                  })
                }
              />

              <Field
                label="Date of birth"
                value={form.date_of_birth}
                onChange={(value) =>
                  setForm({
                    ...form,
                    date_of_birth: value,
                  })
                }
              />
            </div>

            <Field
              label="Address"
              value={form.address}
              onChange={(value) =>
                setForm({
                  ...form,
                  address: value,
                })
              }
            />

            <button
              type="submit"
              className="btn primary full"
              disabled={busy}
            >
              {busy
                ? "Creating..."
                : "Create customer"}
            </button>
          </form>
        </Modal>
      )}
    </section>
  );
}

/* =========================================================
   CASE DETAIL
========================================================= */

function CaseDetail({
  caseId,
  goBack,
  user,
}) {
  const [summary, setSummary] =
    useState(null);

  const [tab, setTab] =
    useState("overview");

  const [uploading, setUploading] =
    useState(false);

  const [docType, setDocType] =
    useState("passport");

  const [file, setFile] =
    useState(null);

  const [review, setReview] =
    useState(null);

  const [reviewer, setReviewer] =
    useState("Demo Reviewer");

  const [comment, setComment] =
    useState("");

  const [busy, setBusy] =
    useState(false);

  const [running, setRunning] =
    useState(false);

  const [runMessage, setRunMessage] =
    useState("");

  const load = async () => {
    if (!caseId) return;

    try {
      const summaryData =
        await api(
          `/api/cases/${caseId}/summary`
        );

      setSummary(summaryData);

      if (user?.role !== "CUSTOMER") {
        const pending =
          await api(
            "/api/reviews/pending"
          );

        const list = Array.isArray(pending)
          ? pending
          : [];

        setReview(
          list.find(
            (item) =>
              Number(item.case_id) ===
              Number(caseId)
          ) || null
        );
      } else {
        setReview(null);
      }
    } catch (error) {
      console.error(
        "Case detail loading error:",
        error
      );
    }
  };

  useEffect(() => {
    load();

    const timer = setInterval(
      load,
      4000
    );

    return () =>
      clearInterval(timer);
  }, [caseId, user?.role]);

  if (!summary) {
    return <Loading full />;
  }

  const currentCase =
    summary.case || {};

  const customer =
    summary.customer || {};

  const documents =
    Array.isArray(summary.documents)
      ? summary.documents
      : [];

  const evidence =
    Array.isArray(summary.evidence)
      ? summary.evidence
      : [];

  const timeline =
    Array.isArray(summary.timeline)
      ? summary.timeline
      : [];

  const doUpload = async (event) => {
    event.preventDefault();

    if (!file) {
      alert("Please choose a document.");
      return;
    }

    setUploading(true);

    const formData = new FormData();

    formData.append(
      "case_id",
      String(caseId)
    );

    formData.append(
      "document_type",
      docType
    );

    formData.append(
      "file",
      file
    );

    try {
      await api(
        "/api/documents/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      setFile(null);

      await load();
    } catch (error) {
      alert(
        error.message ||
          "Unable to upload document."
      );
    } finally {
      setUploading(false);
    }
  };

  const runWorkflow = async () => {
    setRunning(true);

    setRunMessage(
      "Starting agent workflow..."
    );

    try {
      const latestDocs =
        await api(
          `/api/documents/case/${caseId}`
        );

      if (
        !Array.isArray(latestDocs) ||
        !latestDocs.length
      ) {
        throw new Error(
          "Upload a document first."
        );
      }

      const result = await api(
        `/api/workflow/cases/${caseId}/run`,
        {
          method: "POST",
          body: JSON.stringify({
            document_id:
              latestDocs[0].id,
          }),
        }
      );

      setRunMessage(
        `Workflow finished: ${pretty(
          result?.status ||
            "completed"
        )}${
          result?.human_review_reason
            ? ` · ${result.human_review_reason}`
            : ""
        }`
      );

      await load();
    } catch (error) {
      setRunMessage(
        error.message ||
          "Workflow failed."
      );
    } finally {
      setRunning(false);
    }
  };

  const decide = async (decision) => {
    if (!review?.id) {
      alert(
        "No pending review exists for this case."
      );
      return;
    }

    setBusy(true);

    try {
      await api(
        `/api/reviews/${review.id}/decision`,
        {
          method: "POST",
          body: JSON.stringify({
            decision,
            reviewer_name:
              reviewer,
            reviewer_comment:
              comment || null,
          }),
        }
      );

      setReview(null);

      await load();
    } catch (error) {
      alert(
        error.message ||
          "Unable to submit review decision."
      );
    } finally {
      setBusy(false);
    }
  };

  return (
    <section>
      <div className="detail-head">
        <button
          type="button"
          className="back-btn"
          onClick={goBack}
        >
          <Icon name="back" />
          Back
        </button>

        <div className="case-title">
          <div className="eyebrow">
            CASE{" "}
            {currentCase.case_number ||
              `#${currentCase.id}`}
          </div>

          <h1>
            {customer.name ||
              "Unknown customer"}
          </h1>

          <p>
            {customer.email ||
              "No email"}{" "}
            · Created{" "}
            {formatDate(
              currentCase.created_at
            )}
          </p>
        </div>

        <div className="head-status">
          {user?.role !== "CUSTOMER" && (
            <button
              type="button"
              className="btn primary"
              onClick={runWorkflow}
              disabled={running}
            >
              {running ? (
                <>
                  <span className="mini-spinner"></span>
                  Running agents...
                </>
              ) : (
                <>
                  <Icon name="activity" />
                  Run KYC agents
                </>
              )}
            </button>
          )}

          <Badge
            value={currentCase.status}
          />

          <div className="risk-box">
            <small>
              Risk score
            </small>

            <b>
              {currentCase.risk_level
                ? `${currentCase.risk_score ?? "—"} · ${currentCase.risk_level}`
                : "Not assessed"}
            </b>
          </div>
        </div>
      </div>

      {runMessage && (
        <div
          className={`run-message ${
            runMessage
              .toLowerCase()
              .includes("failed") ||
            runMessage
              .toLowerCase()
              .includes("error")
              ? "error"
              : ""
          }`}
        >
          <Icon name="activity" />
          <span>{runMessage}</span>
        </div>
      )}

      <AgentPipeline
        summary={summary}
        running={running}
      />

      <div className="case-tabs">
        {[
          ["overview", "Overview"],
          ["documents", "Documents"],
          ["evidence", "Evidence"],
          ["timeline", "Timeline"],
          ["review", "Human review"],
        ].map(([id, label]) => (
          <button
            type="button"
            className={
              tab === id ? "active" : ""
            }
            onClick={() => setTab(id)}
            key={id}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="detail-grid">
          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>
                  Decision summary
                </h2>

                <span>
                  Latest agent outputs
                </span>
              </div>
            </div>

            <AgentCard
              title="Identity verification"
              icon="user"
              data={summary.identity}
            />

            <AgentCard
              title="Risk assessment"
              icon="shield"
              data={summary.risk}
            />

            <AgentCard
              title="Final decision"
              icon="check"
              data={summary.decision}
            />
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>
                  Customer profile
                </h2>

                <span>
                  Verified onboarding information
                </span>
              </div>
            </div>

            <Info
              label="Name"
              value={customer.name}
            />

            <Info
              label="Email"
              value={customer.email}
            />

            <Info
              label="Phone"
              value={customer.phone}
            />

            <Info
              label="Date of birth"
              value={
                customer.date_of_birth
              }
            />

            <Info
              label="Address"
              value={customer.address}
            />
          </div>
        </div>
      )}

      {tab === "documents" && (
        <div className="detail-grid">
          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>Documents</h2>

                <span>
                  {documents.length} uploaded
                </span>
              </div>
            </div>

            {documents.length ? (
              documents.map((document) => (
                <div
                  className="doc-row"
                  key={document.id}
                >
                  <div className="doc-icon">
                    <Icon name="file" />
                  </div>

                  <div className="grow">
                    <b>
                      {pretty(
                        document.document_type
                      )}
                    </b>

                    <small>
                      {document.file_name} ·
                      extraction{" "}
                      {pretty(
                        document.extraction_status
                      )}
                    </small>

                    <button
                      type="button"
                      className="btn small"
                      onClick={() =>
                        openOriginalDocument(
                          document.id
                        ).catch((error) =>
                          alert(
                            error.message
                          )
                        )
                      }
                    >
                      View original
                    </button>

                    {document.extracted_data && (
                      <details>
                        <summary>
                          View OCR output
                        </summary>

                        <pre className="ocr-output">
                          {typeof document.extracted_data ===
                          "string"
                            ? document.extracted_data
                            : JSON.stringify(
                                document.extracted_data,
                                null,
                                2
                              )}
                        </pre>
                      </details>
                    )}
                  </div>

                  <Badge
                    value={document.status}
                  />
                </div>
              ))
            ) : (
              <Empty text="No documents uploaded" />
            )}
          </div>

          {user?.role === "CUSTOMER" ? (
            <div className="panel">
              <div className="panel-head">
                <div>
                  <h2>
                    Customer document intake
                  </h2>

                  <span>
                    Self-service upload
                  </span>
                </div>
              </div>

              <p className="muted">
                Upload documents from the
                Customer Settings page.
              </p>
            </div>
          ) : (
            <div className="panel">
              <div className="panel-head">
                <div>
                  <h2>
                    Upload document
                  </h2>

                  <span>
                    PDF, PNG or JPG
                  </span>
                </div>
              </div>

              <form
                className="upload-box"
                onSubmit={doUpload}
              >
                <label className="select-label">
                  Document type

                  <select
                    value={docType}
                    onChange={(event) =>
                      setDocType(
                        event.target.value
                      )
                    }
                  >
                    {[
                      "passport",
                      "national_id",
                      "driving_license",
                      "address_proof",
                      "bank_statement",
                    ].map((type) => (
                      <option
                        key={type}
                        value={type}
                      >
                        {type}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="dropzone">
                  <Icon
                    name="upload"
                    size={28}
                  />

                  <b>
                    {file
                      ? file.name
                      : "Choose a file"}
                  </b>

                  <small>
                    Drag & drop or browse
                  </small>

                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(event) =>
                      setFile(
                        event.target
                          .files?.[0] || null
                      )
                    }
                  />
                </label>

                <button
                  type="submit"
                  className="btn primary full"
                  disabled={
                    !file || uploading
                  }
                >
                  {uploading
                    ? "Uploading..."
                    : "Upload document"}
                </button>
              </form>
            </div>
          )}
        </div>
      )}

      {tab === "evidence" && (
        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>
                Evidence ledger
              </h2>

              <span>
                Agent-grounded evidence
                attached to this case
              </span>
            </div>
          </div>

          {evidence.length ? (
            evidence.map((item) => (
              <div
                className="evidence-row"
                key={item.id}
              >
                <div className="evidence-dot"></div>

                <div className="grow">
                  <div className="evidence-top">
                    <b>
                      {pretty(
                        item.evidence_type
                      )}
                    </b>

                    <span>
                      {item.agent_name}
                    </span>
                  </div>

                  <p>
                    {item.explanation ||
                      "No explanation provided."}
                  </p>

                  <small>
                    {item.field_name
                      ? `Field: ${item.field_name} · `
                      : ""}

                    {item.result || "—"}

                    {item.confidence != null
                      ? ` · ${(
                          Number(
                            item.confidence
                          ) * 100
                        ).toFixed(
                          0
                        )}% confidence`
                      : ""}
                  </small>
                </div>
              </div>
            ))
          ) : (
            <Empty text="No evidence recorded" />
          )}
        </div>
      )}

      {tab === "timeline" && (
        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>
                Case timeline
              </h2>

              <span>
                Audit trail and review events
              </span>
            </div>
          </div>

          <div className="timeline">
            {timeline.map(
              (item, index) => (
                <div
                  className="timeline-item"
                  key={`${item.timestamp || "event"}-${index}`}
                >
                  <div className="timeline-line"></div>

                  <div className="timeline-dot"></div>

                  <div>
                    <div className="timeline-title">
                      <b>
                        {pretty(
                          item.title
                        )}
                      </b>

                      <span>
                        {item.agent ||
                          item.reviewer ||
                          "system"}
                      </span>
                    </div>

                    <p>
                      {item.description ||
                        "—"}
                    </p>

                    <small>
                      {formatDateTime(
                        item.timestamp
                      )}
                    </small>
                  </div>
                </div>
              )
            )}

            {!timeline.length && (
              <Empty text="No timeline events" />
            )}
          </div>
        </div>
      )}

      {tab === "review" && (
        <div className="detail-grid">
          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>
                  Human review
                </h2>

                <span>
                  Make a final decision when
                  the agent workflow requires
                  escalation.
                </span>
              </div>
            </div>

            {review ? (
              <>
                <div className="review-callout">
                  <Icon name="shield" />

                  <div>
                    <b>
                      Review #{review.id} is
                      pending
                    </b>

                    <span>
                      Review the OCR document
                      and evidence, then select
                      Approve or Reject.
                    </span>
                  </div>
                </div>

                <Field
                  label="Reviewer name"
                  value={reviewer}
                  onChange={setReviewer}
                />

                <label className="select-label">
                  Comment

                  <textarea
                    rows="5"
                    placeholder="Add decision rationale..."
                    value={comment}
                    onChange={(event) =>
                      setComment(
                        event.target.value
                      )
                    }
                  />
                </label>

                <div className="decision-actions">
                  <button
                    type="button"
                    className="btn danger"
                    disabled={busy}
                    onClick={() =>
                      decide("REJECT")
                    }
                  >
                    <Icon name="x" />
                    Reject
                  </button>

                  <button
                    type="button"
                    className="btn success"
                    disabled={busy}
                    onClick={() =>
                      decide("APPROVE")
                    }
                  >
                    <Icon name="check" />
                    Approve
                  </button>
                </div>
              </>
            ) : summary.human_review
                ?.status ===
              "COMPLETED" ? (
              <div className="review-callout">
                <Icon
                  name={
                    summary.human_review
                      .decision ===
                    "APPROVE"
                      ? "check"
                      : "x"
                  }
                />

                <div>
                  <b>
                    Human review completed —{" "}
                    {summary.human_review
                      .decision ===
                    "APPROVE"
                      ? "Approved"
                      : "Rejected"}
                  </b>

                  <span>
                    Reviewer:{" "}
                    {summary.human_review
                      .reviewer_name ||
                      "—"}{" "}
                    ·{" "}
                    {summary.human_review
                      .reviewer_comment ||
                      "No comment provided."}
                  </span>
                </div>
              </div>
            ) : (
              <Empty text="No pending human review for this case." />
            )}
          </div>

          <div className="panel">
            <div className="panel-head">
              <div>
                <h2>
                  Decision context
                </h2>

                <span>
                  What the agents found
                </span>
              </div>
            </div>

            <AgentCard
              title="Identity"
              data={summary.identity}
            />

            <AgentCard
              title="Risk"
              data={summary.risk}
            />
          </div>
        </div>
      )}
    </section>
  );
}

/* =========================================================
   AGENT PIPELINE
========================================================= */

function AgentPipeline({
  summary,
  running,
}) {
  const steps = [
    [
      "document_agent",
      "Document Agent",
      "document",
      summary.documents?.length > 0,
      summary.documents?.[0]
        ?.extraction_status,
    ],

    [
      "identity_agent",
      "Identity Agent",
      "user",
      !!summary.identity,
      summary.identity?.result,
    ],

    [
      "risk_agent",
      "Risk Agent",
      "shield",
      !!summary.risk,
      summary.risk?.result,
    ],

    [
      "decision_agent",
      "Decision Agent",
      "check",
      !!summary.decision,
      summary.decision?.result,
    ],
  ];

  const active =
    summary.case?.status ===
      "IN_PROGRESS" || running;

  return (
    <div className="agent-pipeline">
      {steps.map(
        (
          [
            id,
            label,
            icon,
            done,
            result,
          ],
          index
        ) => (
          <React.Fragment key={id}>
            <div
              className={`pipeline-step ${
                done ? "done" : ""
              } ${
                active && !done
                  ? "pending"
                  : ""
              }`}
            >
              <div className="pipeline-icon">
                <Icon name={icon} />
              </div>

              <div>
                <b>{label}</b>

                <small>
                  {done
                    ? result ||
                      "Completed"
                    : active
                    ? "Waiting"
                    : "Not run"}
                </small>
              </div>
            </div>

            {index <
              steps.length - 1 && (
              <div
                className={`pipeline-connector ${
                  done ? "done" : ""
                }`}
              ></div>
            )}
          </React.Fragment>
        )
      )}
    </div>
  );
}

/* =========================================================
   AGENT CARD
========================================================= */

function AgentCard({
  title,
  icon = "activity",
  data,
}) {
  return (
    <div className="agent-card">
      <div className="agent-icon">
        <Icon name={icon} />
      </div>

      <div className="grow">
        <b>{title}</b>

        {data ? (
          <>
            <p>
              {data.explanation ||
                data.event_message ||
                data.result ||
                "Result recorded."}
            </p>

            <small>
              {data.result || "—"}

              {data.confidence != null
                ? ` · ${(
                    Number(
                      data.confidence
                    ) * 100
                  ).toFixed(
                    0
                  )}% confidence`
                : ""}
            </small>
          </>
        ) : (
          <p className="muted">
            No result recorded yet.
          </p>
        )}
      </div>
    </div>
  );
}

/* =========================================================
   BASIC COMPONENTS
========================================================= */

function Info({
  label,
  value,
}) {
  return (
    <div className="info-row">
      <span>{label}</span>
      <b>{value || "—"}</b>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
  required = false,
}) {
  return (
    <label className="field">
      <span>
        {label}
        {required && " *"}
      </span>

      <input
        type={type}
        required={required}
        value={value || ""}
        onChange={(event) =>
          onChange(event.target.value)
        }
      />
    </label>
  );
}

function Modal({
  title,
  onClose,
  children,
}) {
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(event) => {
        if (
          event.target ===
          event.currentTarget
        ) {
          onClose();
        }
      }}
    >
      <div className="modal">
        <div className="modal-head">
          <h2>{title}</h2>

          <button
            type="button"
            onClick={onClose}
          >
            <Icon name="x" />
          </button>
        </div>

        {children}
      </div>
    </div>
  );
}

function Empty({ text }) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon name="file" />
      </div>

      <b>{text}</b>

      <span>
        Nothing to display here yet.
      </span>
    </div>
  );
}

function Loading({
  full = false,
}) {
  return (
    <div
      className={`loading ${
        full ? "full" : ""
      }`}
    >
      <div className="spinner"></div>
      <span>Loading...</span>
    </div>
  );
}

/* =========================================================
   AUTHENTICATION SCREEN
   IMPORTANT FIX:
   Never access data.access_token before
   checking that data exists.
========================================================= */

function AuthScreen({
  onAuthenticated,
}) {
  const [mode, setMode] =
    useState("login");

  const [form, setForm] =
    useState({
      login: "",
      username: "",
      email: "",
      password: "",
      full_name: "",
      phone: "",
      date_of_birth: "",
      address: "",
    });

  const [busy, setBusy] =
    useState(false);

  const [error, setError] =
    useState("");

  const submit = async (event) => {
    event.preventDefault();

    if (busy) return;

    setBusy(true);
    setError("");

    try {
      const path =
        mode === "login"
          ? "/api/auth/login"
          : "/api/auth/register";

      const body =
        mode === "login"
          ? {
              login:
                form.login.trim(),
              password:
                form.password,
            }
          : {
              username:
                form.username.trim(),
              email:
                form.email.trim(),
              password:
                form.password,
              full_name:
                form.full_name.trim(),
              phone:
                form.phone.trim(),
              date_of_birth:
                form.date_of_birth.trim(),
              address:
                form.address.trim(),
            };

      const data = await api(path, {
        method: "POST",
        body: JSON.stringify(body),
      });

      /*
       * IMPORTANT:
       * The previous version directly did:
       *
       * data.access_token
       *
       * which caused:
       *
       * Cannot read properties of null
       * (reading 'access_token')
       */

      console.log(
        "OnboardAI AUTH RESPONSE:",
        data
      );

      if (!data) {
        throw new Error(
          "The authentication API returned an empty response. Please check the Railway backend response."
        );
      }

      /*
       * Some FastAPI validation responses can
       * arrive as an object rather than a token.
       */
      if (!data.access_token) {
        const backendMessage =
          Array.isArray(data.detail)
            ? data.detail
                .map(
                  (item) =>
                    item?.msg ||
                    String(item)
                )
                .join(", ")
            : data.detail ||
              data.message ||
              data.error;

        throw new Error(
          backendMessage ||
            "Login response does not contain access_token."
        );
      }

      if (!data.user) {
        throw new Error(
          "Authentication succeeded but the response does not contain user information."
        );
      }

      localStorage.setItem(
        "onboardai_token",
        data.access_token
      );

      onAuthenticated(data.user);
    } catch (error) {
      console.error(
        "OnboardAI authentication error:",
        error
      );

      setError(
        error?.message ||
          "Authentication failed. Please try again."
      );
    } finally {
      setBusy(false);
    }
  };

  const switchMode = (nextMode) => {
    setMode(nextMode);
    setError("");
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="brand auth-brand">
          <div className="brand-mark">
            O
          </div>

          <div>
            <strong>
              OnboardAI
            </strong>

            <span>
              Secure KYC onboarding
            </span>
          </div>
        </div>

        <div className="auth-tabs">
          <button
            type="button"
            className={
              mode === "login"
                ? "active"
                : ""
            }
            onClick={() =>
              switchMode("login")
            }
          >
            Sign in
          </button>

          <button
            type="button"
            className={
              mode === "register"
                ? "active"
                : ""
            }
            onClick={() =>
              switchMode("register")
            }
          >
            Register
          </button>
        </div>

        <h1>
          {mode === "login"
            ? "Welcome back"
            : "Create your account"}
        </h1>

        <p>
          {mode === "login"
            ? "Sign in to continue your KYC journey."
            : "Register as a customer to start your KYC process."}
        </p>

        {error && (
          <div className="run-message error">
            <Icon name="x" />
            <span>
              {error}
            </span>
          </div>
        )}

        <form
          className="form"
          onSubmit={submit}
        >
          {mode === "register" && (
            <>
              <Field
                label="Full name"
                required
                value={form.full_name}
                onChange={(value) =>
                  setForm({
                    ...form,
                    full_name: value,
                  })
                }
              />

              <Field
                label="Username"
                required
                value={form.username}
                onChange={(value) =>
                  setForm({
                    ...form,
                    username: value,
                  })
                }
              />

              <Field
                label="Email"
                type="email"
                required
                value={form.email}
                onChange={(value) =>
                  setForm({
                    ...form,
                    email: value,
                  })
                }
              />

              <div className="form-row">
                <Field
                  label="Phone"
                  value={form.phone}
                  onChange={(value) =>
                    setForm({
                      ...form,
                      phone: value,
                    })
                  }
                />

                <Field
                  label="Date of birth"
                  value={
                    form.date_of_birth
                  }
                  onChange={(value) =>
                    setForm({
                      ...form,
                      date_of_birth:
                        value,
                    })
                  }
                />
              </div>

              <Field
                label="Address"
                value={form.address}
                onChange={(value) =>
                  setForm({
                    ...form,
                    address: value,
                  })
                }
              />
            </>
          )}

          {mode === "login" && (
            <Field
              label="Username or email"
              required
              value={form.login}
              onChange={(value) =>
                setForm({
                  ...form,
                  login: value,
                })
              }
            />
          )}

          <Field
            label="Password"
            type="password"
            required
            value={form.password}
            onChange={(value) =>
              setForm({
                ...form,
                password: value,
              })
            }
          />

          <button
            type="submit"
            className="btn primary full"
            disabled={busy}
          >
            {busy
              ? "Please wait..."
              : mode === "login"
              ? "Sign in"
              : "Register"}
          </button>
        </form>
      </div>
    </div>
  );
}

/* =========================================================
   CAMERA CAPTURE
========================================================= */

function CameraCapture({
  onCapture,
  onClose,
}) {
  const videoRef =
    useRef(null);

  const canvasRef =
    useRef(null);

  const [stream, setStream] =
    useState(null);

  const [error, setError] =
    useState("");

  const [ready, setReady] =
    useState(false);

  useEffect(() => {
    let active = true;

    const startCamera = async () => {
      try {
        if (
          !navigator.mediaDevices?.getUserMedia
        ) {
          throw new Error(
            "Camera access is not supported by this browser."
          );
        }

        const cameraStream =
          await navigator.mediaDevices.getUserMedia(
            {
              video: {
                facingMode: {
                  ideal: "environment",
                },
                width: {
                  ideal: 1920,
                },
                height: {
                  ideal: 1080,
                },
              },
              audio: false,
            }
          );

        if (!active) {
          cameraStream
            .getTracks()
            .forEach((track) =>
              track.stop()
            );

          return;
        }

        setStream(cameraStream);

        if (videoRef.current) {
          videoRef.current.srcObject =
            cameraStream;

          await videoRef.current.play();

          setReady(true);
        }
      } catch (cameraError) {
        console.error(
          "Camera error:",
          cameraError
        );

        setError(
          cameraError.name ===
            "NotAllowedError"
            ? "Camera permission was denied. Allow camera access and try again."
            : cameraError.message ||
                "Unable to access camera."
        );
      }
    };

    startCamera();

    return () => {
      active = false;

      setStream((current) => {
        current
          ?.getTracks()
          .forEach((track) =>
            track.stop()
          );

        return null;
      });
    };
  }, []);

  const capture = () => {
    const video =
      videoRef.current;

    const canvas =
      canvasRef.current;

    if (
      !video ||
      !canvas ||
      !ready
    ) {
      return;
    }

    canvas.width =
      video.videoWidth || 1280;

    canvas.height =
      video.videoHeight || 720;

    const context =
      canvas.getContext("2d");

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError(
            "Unable to capture the camera image."
          );
          return;
        }

        const capturedFile =
          new File(
            [blob],
            `camera-document-${Date.now()}.jpg`,
            {
              type: "image/jpeg",
              lastModified:
                Date.now(),
            }
          );

        onCapture(capturedFile);

        onClose();
      },
      "image/jpeg",
      0.94
    );
  };

  return (
    <Modal
      title="Capture document with camera"
      onClose={onClose}
    >
      <div className="camera-modal">
        <div className="camera-frame">
          <video
            ref={videoRef}
            playsInline
            muted
          />

          <div className="camera-guide">
            <span></span>
          </div>
        </div>

        {error ? (
          <div className="run-message error">
            <Icon name="x" />
            <span>{error}</span>
          </div>
        ) : (
          <p className="muted">
            Place the full document inside
            the frame. Keep it flat, well lit
            and readable.
          </p>
        )}

        <canvas
          ref={canvasRef}
          className="hidden-canvas"
        />

        <div className="camera-actions">
          <button
            type="button"
            className="btn secondary"
            onClick={onClose}
          >
            Cancel
          </button>

          <button
            type="button"
            className="btn primary"
            disabled={
              !ready || !!error
            }
            onClick={capture}
          >
            Capture & use photo
          </button>
        </div>
      </div>
    </Modal>
  );
}

/* =========================================================
   CUSTOMER PROFILE
========================================================= */

function CustomerProfile({
  user,
  openCase,
}) {
  const [customer, setCustomer] =
    useState(null);

  const [cases, setCases] =
    useState([]);

  const [caseId, setCaseId] =
    useState(null);

  const [docs, setDocs] =
    useState([]);

  const [docType, setDocType] =
    useState("passport");

  const [file, setFile] =
    useState(null);

  const [uploading, setUploading] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const [camera, setCamera] =
    useState(false);

  const load = async () => {
    try {
      if (!user?.customer_id) {
        throw new Error(
          "Your account is not linked to a customer profile."
        );
      }

      const customerData =
        await api(
          `/api/customers/${user.customer_id}`
        );

      setCustomer(customerData);

      const caseData =
        await api("/api/cases");

      const caseList = Array.isArray(
        caseData
      )
        ? caseData
        : [];

      setCases(caseList);

      if (
        caseId == null &&
        caseList.length
      ) {
        setCaseId(caseList[0].id);
      }
    } catch (error) {
      setMessage(
        error.message ||
          "Unable to load customer profile."
      );
    }
  };

  useEffect(() => {
    load();

    const timer = setInterval(
      load,
      4000
    );

    return () =>
      clearInterval(timer);
  }, [user?.customer_id]);

  useEffect(() => {
    if (!caseId) return;

    const refreshDocs = async () => {
      try {
        const data = await api(
          `/api/documents/case/${caseId}`
        );

        setDocs(
          Array.isArray(data)
            ? data
            : []
        );
      } catch {
        setDocs([]);
      }
    };

    refreshDocs();

    const timer = setInterval(
      refreshDocs,
      3000
    );

    return () =>
      clearInterval(timer);
  }, [caseId]);

  const start = async () => {
    try {
      if (!user?.customer_id) {
        throw new Error(
          "Customer profile not found."
        );
      }

      const created =
        await api("/api/cases", {
          method: "POST",
          body: JSON.stringify({
            customer_id:
              user.customer_id,
          }),
        });

      setCases((current) => [
        created,
        ...current,
      ]);

      setCaseId(created.id);

      setMessage(
        `KYC case ${
          created.case_number ||
          created.id
        } created. Upload your document below.`
      );
    } catch (error) {
      setMessage(
        error.message ||
          "Unable to create KYC case."
      );
    }
  };

  const upload = async (event) => {
    event.preventDefault();

    if (!file) {
      setMessage(
        "Please choose or capture a document first."
      );
      return;
    }

    if (!caseId) {
      setMessage(
        "Please create or select a KYC case first."
      );
      return;
    }

    setUploading(true);

    setMessage(
      "Uploading document and starting OCR..."
    );

    const formData =
      new FormData();

    formData.append(
      "case_id",
      String(caseId)
    );

    formData.append(
      "document_type",
      docType
    );

    formData.append(
      "file",
      file
    );

    try {
      await api(
        "/api/documents/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      setFile(null);

      setMessage(
        "Document uploaded. OCR and KYC processing has started automatically."
      );

      await load();
    } catch (error) {
      setMessage(
        error.message ||
          "Document upload failed."
      );
    } finally {
      setUploading(false);
    }
  };

  if (!customer) {
    return <Loading full />;
  }

  const active =
    cases.find(
      (item) =>
        Number(item.id) ===
        Number(caseId)
    ) || null;

  const status =
    active?.status || "CREATED";

  const step =
    status === "CREATED" ||
    status ===
      "DOCUMENT_COLLECTION"
      ? "Document upload"
      : status ===
          "IN_PROGRESS"
      ? "OCR & automated KYC checks"
      : status ===
            "HUMAN_REVIEW" ||
          status ===
            "WAITING_FOR_HUMAN_REVIEW"
      ? "Human review"
      : status ===
            "APPROVED" ||
          status ===
            "REJECTED" ||
          status ===
            "COMPLETED"
      ? "Completed"
      : "Processing";

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="eyebrow">
            CUSTOMER SETTINGS
          </div>

          <h1>
            My profile & KYC
          </h1>

          <p>
            Upload a document from your
            device or capture it directly
            with your camera. The original
            is retained and OCR starts
            automatically.
          </p>
        </div>

        <button
          type="button"
          className="btn primary"
          onClick={start}
        >
          <Icon name="plus" />
          New KYC case
        </button>
      </div>

      {message && (
        <div className="run-message">
          <Icon name="activity" />
          <span>{message}</span>
        </div>
      )}

      <div className="detail-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>
                My information
              </h2>

              <span>
                Registered customer details
              </span>
            </div>
          </div>

          <Info
            label="Name"
            value={customer.name}
          />

          <Info
            label="Email"
            value={customer.email}
          />

          <Info
            label="Phone"
            value={customer.phone}
          />

          <Info
            label="Date of birth"
            value={
              customer.date_of_birth
            }
          />

          <Info
            label="Address"
            value={customer.address}
          />
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>
                OCR document intake
              </h2>

              <span>
                Upload or capture a clear
                image; OCR reads a copy and
                preserves the original.
              </span>
            </div>
          </div>

          {cases.length ? (
            <>
              <label className="select-label">
                KYC case

                <select
                  value={caseId || ""}
                  onChange={(event) =>
                    setCaseId(
                      Number(
                        event.target.value
                      )
                    )
                  }
                >
                  {cases.map(
                    (item) => (
                      <option
                        value={item.id}
                        key={item.id}
                      >
                        {item.case_number ||
                          `CASE-${item.id}`}{" "}
                        ·{" "}
                        {pretty(
                          item.status
                        )}
                      </option>
                    )
                  )}
                </select>
              </label>

              <form
                className="upload-box"
                onSubmit={upload}
              >
                <label className="select-label">
                  Document type

                  <select
                    value={docType}
                    onChange={(event) =>
                      setDocType(
                        event.target.value
                      )
                    }
                  >
                    {[
                      "passport",
                      "national_id",
                      "driving_license",
                      "address_proof",
                      "bank_statement",
                    ].map(
                      (type) => (
                        <option
                          key={type}
                          value={type}
                        >
                          {type}
                        </option>
                      )
                    )}
                  </select>
                </label>

                <div className="upload-actions">
                  <label className="dropzone">
                    <Icon
                      name="upload"
                      size={28}
                    />

                    <b>
                      {file
                        ? file.name
                        : "Choose a document"}
                    </b>

                    <small>
                      PDF, JPG, PNG, WEBP
                      or TIFF · max 15 MB
                    </small>

                    <input
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg,.webp,.tif,.tiff,image/*"
                      capture="environment"
                      onChange={(event) =>
                        setFile(
                          event.target
                            .files?.[0] ||
                            null
                        )
                      }
                    />
                  </label>

                  <button
                    type="button"
                    className="camera-button"
                    onClick={() =>
                      setCamera(true)
                    }
                  >
                    <span className="camera-icon">
                      ●
                    </span>

                    <b>
                      Use camera
                    </b>

                    <small>
                      Take a document photo
                    </small>
                  </button>
                </div>

                <button
                  type="submit"
                  className="btn primary full"
                  disabled={
                    !file ||
                    uploading
                  }
                >
                  {uploading
                    ? "Uploading & starting OCR..."
                    : "Upload & start OCR"}
                </button>
              </form>
            </>
          ) : (
            <div className="empty">
              <b>
                Start a KYC case first
              </b>

              <span>
                Then you can upload your
                document here.
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <h2>
              Current KYC step
            </h2>

            <span>
              {active?.case_number ||
                "No active case"}
            </span>
          </div>

          <Badge value={status} />
        </div>

        <div className="current-step">
          <div className="eyebrow">
            CURRENT STEP
          </div>

          <h2>{step}</h2>

          <p className="muted">
            {status ===
            "HUMAN_REVIEW"
              ? "Your documents and automated checks are waiting for an analyst/QA reviewer."
              : status ===
                "IN_PROGRESS"
              ? "OCR and the KYC agents are processing your submission."
              : status ===
                "APPROVED"
              ? "Your KYC has been approved."
              : status ===
                "REJECTED"
              ? "Your KYC has been rejected."
              : "Upload your document to begin."}
          </p>
        </div>

        {docs.map((document) => (
          <div
            className="doc-row"
            key={document.id}
          >
            <div className="doc-icon">
              <Icon name="file" />
            </div>

            <div className="grow">
              <b>
                {pretty(
                  document.document_type
                )}
              </b>

              <small>
                {document.file_name} ·
                OCR{" "}
                {pretty(
                  document.extraction_status
                )}
              </small>

              <button
                type="button"
                className="btn small"
                onClick={() =>
                  openOriginalDocument(
                    document.id
                  ).catch((error) =>
                    alert(
                      error.message
                    )
                  )
                }
              >
                View original
              </button>

              {document.extracted_data && (
                <details>
                  <summary>
                    View OCR output
                  </summary>

                  <pre className="ocr-output">
                    {typeof document.extracted_data ===
                    "string"
                      ? document.extracted_data
                      : JSON.stringify(
                          document.extracted_data,
                          null,
                          2
                        )}
                  </pre>
                </details>
              )}
            </div>

            <Badge
              value={document.status}
            />
          </div>
        ))}
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <h2>
              My KYC cases
            </h2>

            <span>
              Live progress
            </span>
          </div>
        </div>

        {cases.length ? (
          cases.map((item) => (
            <div
              className="case-progress"
              key={item.id}
            >
              <div className="customer-top">
                <div className="grow">
                  <b>
                    {item.case_number ||
                      `CASE-${item.id}`}
                  </b>

                  <small>
                    Updated{" "}
                    {formatDateTime(
                      item.updated_at
                    )}
                  </small>
                </div>

                <Badge
                  value={item.status}
                />
              </div>

              <div className="progress-line">
                <span
                  className={
                    item.status !==
                    "CREATED"
                      ? "done"
                      : ""
                  }
                >
                  Document
                </span>

                <span
                  className={
                    [
                      "IN_PROGRESS",
                      "HUMAN_REVIEW",
                      "WAITING_FOR_HUMAN_REVIEW",
                      "APPROVED",
                      "REJECTED",
                      "COMPLETED",
                    ].includes(
                      item.status
                    )
                      ? "done"
                      : ""
                  }
                >
                  Automated checks
                </span>

                <span
                  className={
                    item.status ===
                    "HUMAN_REVIEW"
                      ? "active"
                      : [
                          "APPROVED",
                          "REJECTED",
                          "COMPLETED",
                        ].includes(
                          item.status
                        )
                      ? "done"
                      : ""
                  }
                >
                  Human review
                </span>

                <span
                  className={
                    [
                      "APPROVED",
                      "REJECTED",
                      "COMPLETED",
                    ].includes(
                      item.status
                    )
                      ? "done"
                      : ""
                  }
                >
                  Decision
                </span>
              </div>

              <button
                type="button"
                className="btn small"
                onClick={() =>
                  openCase(item.id)
                }
              >
                View KYC details{" "}
                <Icon
                  name="arrow"
                  size={14}
                />
              </button>
            </div>
          ))
        ) : (
          <Empty text="No KYC cases yet" />
        )}
      </div>

      {camera && (
        <CameraCapture
          onCapture={(capturedFile) => {
            setFile(capturedFile);

            setMessage(
              "Camera photo captured. Review the filename below, then upload to start OCR."
            );
          }}
          onClose={() =>
            setCamera(false)
          }
        />
      )}
    </section>
  );
}

/* =========================================================
   ADMIN USERS
========================================================= */

function AdminUsers() {
  const [users, setUsers] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const load = async () => {
    setLoading(true);

    try {
      const data =
        await api(
          "/api/auth/users"
        );

      setUsers(
        Array.isArray(data)
          ? data
          : []
      );
    } catch (error) {
      alert(
        error.message ||
          "Unable to load users."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const update = async (
    user,
    field,
    value
  ) => {
    try {
      const updated =
        await api(
          `/api/auth/users/${user.id}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              role:
                field === "role"
                  ? value
                  : user.role,

              active:
                field === "active"
                  ? value
                  : user.active,
            }),
          }
        );

      setUsers((current) =>
        current.map((item) =>
          item.id === user.id
            ? updated
            : item
        )
      );
    } catch (error) {
      alert(
        error.message ||
          "Unable to update user."
      );
    }
  };

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="eyebrow">
            ADMINISTRATION
          </div>

          <h1>
            User management
          </h1>

          <p>
            Manage customer, analyst, QA
            and administrator access.
          </p>
        </div>

        <button
          type="button"
          className="btn secondary"
          onClick={load}
        >
          <Icon name="refresh" />
          Refresh
        </button>
      </div>

      <div className="panel">
        {loading ? (
          <Loading />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>User</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Customer</th>
                </tr>
              </thead>

              <tbody>
                {users.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <b>
                        {user.full_name ||
                          user.username}
                      </b>

                      <small>
                        @{user.username}
                      </small>
                    </td>

                    <td>
                      {user.email}
                    </td>

                    <td>
                      <select
                        value={user.role}
                        onChange={(event) =>
                          update(
                            user,
                            "role",
                            event.target
                              .value
                          )
                        }
                      >
                        {[
                          "CUSTOMER",
                          "ANALYST",
                          "QA",
                          "ADMIN",
                        ].map((role) => (
                          <option
                            key={role}
                            value={role}
                          >
                            {role}
                          </option>
                        ))}
                      </select>
                    </td>

                    <td>
                      <button
                        type="button"
                        className="btn small"
                        onClick={() =>
                          update(
                            user,
                            "active",
                            !user.active
                          )
                        }
                      >
                        {user.active
                          ? "Active"
                          : "Disabled"}
                      </button>
                    </td>

                    <td>
                      {user.customer_id
                        ? `CUST-${String(
                            user.customer_id
                          ).padStart(
                            6,
                            "0"
                          )}`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

/* =========================================================
   EMAIL NOTIFICATIONS
========================================================= */

function EmailNotifications() {
  const [items, setItems] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const [recipient, setRecipient] =
    useState("");

  const [sending, setSending] =
    useState(false);

  const [message, setMessage] =
    useState("");

  const load = async () => {
    setLoading(true);

    try {
      const data =
        await api(
          "/api/notifications/emails"
        );

      setItems(
        Array.isArray(data)
          ? data
          : []
      );
    } catch (error) {
      alert(
        error.message ||
          "Unable to load email notifications."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const test = async () => {
    const email =
      recipient.trim();

    if (!email) {
      setMessage(
        "Enter a test recipient email."
      );
      return;
    }

    setSending(true);
    setMessage("");

    try {
      await api(
        "/api/notifications/test-email",
        {
          method: "POST",
          body: JSON.stringify({
            recipient: email,
          }),
        }
      );

      setMessage(
        "SMTP test email sent successfully."
      );

      setRecipient("");

      await load();
    } catch (error) {
      setMessage(
        error.message ||
          "Unable to send test email."
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="eyebrow">
            NOTIFICATIONS
          </div>

          <h1>
            Email delivery
          </h1>

          <p>
            Audit registration and KYC
            notifications and test SMTP
            without changing KYC data.
          </p>
        </div>

        <button
          type="button"
          className="btn secondary"
          onClick={load}
        >
          <Icon name="refresh" />
          Refresh
        </button>
      </div>

      <div className="panel smtp-test">
        <div>
          <b>
            SMTP connection test
          </b>

          <span>
            Send a real test message using
            the configured SMTP account.
          </span>
        </div>

        <div className="smtp-test-form">
          <input
            type="email"
            placeholder="test recipient@example.com"
            value={recipient}
            onChange={(event) =>
              setRecipient(
                event.target.value
              )
            }
          />

          <button
            type="button"
            className="btn primary"
            onClick={test}
            disabled={sending}
          >
            {sending
              ? "Sending..."
              : "Send test email"}
          </button>
        </div>

        {message && (
          <div className="run-message">
            <Icon name="activity" />
            <span>{message}</span>
          </div>
        )}
      </div>

      <div className="panel">
        {loading ? (
          <Loading />
        ) : !items.length ? (
          <Empty text="No email notifications yet" />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Recipient</th>
                  <th>Subject</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Error</th>
                </tr>
              </thead>

              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>
                      {pretty(
                        item.notification_type
                      )}
                    </td>

                    <td>
                      {item.recipient_email}
                    </td>

                    <td>
                      {item.subject}
                    </td>

                    <td>
                      <Badge
                        value={item.status}
                      />
                    </td>

                    <td>
                      {formatDateTime(
                        item.created_at
                      )}
                    </td>

                    <td>
                      {item.error_message ||
                        "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

/* =========================================================
   REVIEW QUEUE
========================================================= */

function ReviewQueue({
  openCase,
}) {
  const [reviews, setReviews] =
    useState([]);

  const [loading, setLoading] =
    useState(true);

  const load = async () => {
    setLoading(true);

    try {
      const data =
        await api(
          "/api/reviews/pending"
        );

      setReviews(
        Array.isArray(data)
          ? data
          : []
      );
    } catch (error) {
      console.error(
        "Review queue error:",
        error
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();

    const timer = setInterval(
      load,
      4000
    );

    return () =>
      clearInterval(timer);
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="eyebrow">
            HUMAN REVIEW
          </div>

          <h1>
            Review queue
          </h1>

          <p>
            Customer-submitted documents,
            OCR output and automated checks
            waiting for a final decision.
          </p>
        </div>

        <button
          type="button"
          className="btn secondary"
          onClick={load}
        >
          <Icon name="refresh" />
          Refresh
        </button>
      </div>

      <div className="panel">
        {loading ? (
          <Loading />
        ) : !reviews.length ? (
          <Empty text="No pending human reviews" />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Review</th>
                  <th>Case</th>
                  <th>Customer</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {reviews.map(
                  (review) => (
                    <tr key={review.id}>
                      <td>
                        <b>
                          Review #
                          {review.id}
                        </b>
                      </td>

                      <td>
                        CASE-
                        {review.case_id}
                      </td>

                      <td>
                        Awaiting reviewer
                      </td>

                      <td>
                        <Badge value="PENDING" />
                      </td>

                      <td>
                        <button
                          type="button"
                          className="btn small"
                          onClick={() =>
                            openCase(
                              review.case_id
                            )
                          }
                        >
                          Open documents &
                          review{" "}
                          <Icon
                            name="arrow"
                            size={14}
                          />
                        </button>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}

/* =========================================================
   AGENT MONITORING
========================================================= */

function AgentMonitoring() {
  const [agents, setAgents] =
    useState([]);

  const [jobs, setJobs] =
    useState([]);

  const [stats, setStats] =
    useState(null);

  const load = async () => {
    try {
      const [
        agentData,
        jobData,
        statsData,
      ] = await Promise.all([
        api(
          "/api/dashboard/agents"
        ),

        api(
          "/api/workflow/jobs"
        ),

        api(
          "/api/dashboard/stats"
        ),
      ]);

      setAgents(
        Array.isArray(agentData)
          ? agentData
          : []
      );

      setJobs(
        Array.isArray(jobData)
          ? jobData
          : []
      );

      setStats(statsData);
    } catch (error) {
      console.error(
        "Agent monitoring error:",
        error
      );
    }
  };

  useEffect(() => {
    load();

    const timer = setInterval(
      load,
      3000
    );

    return () =>
      clearInterval(timer);
  }, []);

  return (
    <section>
      <div className="page-head">
        <div>
          <div className="eyebrow">
            SUPERVISOR / OBSERVABILITY
          </div>

          <h1>
            Agent monitoring
          </h1>

          <p>
            Live supervisor routing,
            durable KYC jobs, worker latency
            and workflow health.
          </p>
        </div>

        <button
          type="button"
          className="btn secondary"
          onClick={load}
        >
          <Icon name="refresh" />
          Refresh
        </button>
      </div>

      <div className="stats-grid">
        <StatCard
          label="Queued jobs"
          value={
            stats?.queued_jobs ??
            "—"
          }
          hint="Durable queue"
          icon="clock"
        />

        <StatCard
          label="Failed jobs"
          value={
            stats?.failed_jobs ??
            "—"
          }
          hint="Retry exhausted"
          icon="x"
        />

        <StatCard
          label="Open reviews"
          value={
            stats?.open_reviews ??
            "—"
          }
          hint="Human-in-the-loop"
          icon="shield"
        />

        <StatCard
          label="Total cases"
          value={
            stats?.total_cases ??
            "—"
          }
          hint="Current scope"
          icon="folder"
        />
      </div>

      <div className="section-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>
                Target-state workers
              </h2>

              <span>
                Runtime events recorded
                from the supervisor
              </span>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Agent</th>
                  <th>Runs</th>
                  <th>
                    Avg latency
                  </th>
                  <th>
                    Last run
                  </th>
                </tr>
              </thead>

              <tbody>
                {agents.length ? (
                  agents.map(
                    (agent) => (
                      <tr
                        key={
                          agent.agent_name
                        }
                      >
                        <td>
                          <b>
                            {
                              agent.agent_name
                            }
                          </b>
                        </td>

                        <td>
                          {agent.runs}
                        </td>

                        <td>
                          {agent.avg_duration_ms
                            ? `${Number(
                                agent.avg_duration_ms
                              ).toFixed(
                                1
                              )} ms`
                            : "—"}
                        </td>

                        <td>
                          {agent.last_run ||
                            "—"}
                        </td>
                      </tr>
                    )
                  )
                ) : (
                  <tr>
                    <td colSpan="4">
                      No agent events yet.
                      Run a KYC case.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <h2>
                Durable workflow queue
              </h2>

              <span>
                Survives API restarts
              </span>
            </div>
          </div>

          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Job</th>
                  <th>Case</th>
                  <th>Status</th>
                  <th>Attempts</th>
                </tr>
              </thead>

              <tbody>
                {jobs.length ? (
                  jobs
                    .slice(0, 15)
                    .map((job) => (
                      <tr
                        key={job.id}
                      >
                        <td>
                          #{job.id}
                        </td>

                        <td>
                          {job.case_id}
                        </td>

                        <td>
                          <Badge
                            value={
                              job.status
                            }
                          />
                        </td>

                        <td>
                          {job.attempts}/
                          {
                            job.max_attempts
                          }
                        </td>
                      </tr>
                    ))
                ) : (
                  <tr>
                    <td colSpan="4">
                      No workflow jobs yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-head">
          <div>
            <h2>
              Supervisor architecture
            </h2>

            <span>
              Integrated target-state
              control plane
            </span>
          </div>
        </div>

        <div className="architecture">
          <div className="archbox supervisor">
            AI ORCHESTRATOR /
            SUPERVISOR

            <small>
              Journey context · routing ·
              shared state · checkpoints ·
              HITL
            </small>
          </div>

          <div className="agentgrid">
            {[
              "Outreach Agent",
              "Data Intake Agent",
              "Document Intelligence",
              "Identity Verification",
              "Screening",
              "Risk Scoring",
              "Anomaly & Alert",
              "Decision",
              "Monitoring",
            ].map((name) => (
              <div
                className="agent"
                key={name}
              >
                {name}

                <small>
                  Worker
                </small>
              </div>
            ))}
          </div>

          <div className="archbox">
            KNOWLEDGE / POLICY /
            INTEGRATION

            <small>
              LlamaIndex · ChromaDB · Policy
              Store · MCP Tool Gateway ·
              Evidence · Audit
            </small>
          </div>

          <div className="agentgrid">
            <div className="agent">
              Groq
              <small>
                Assistive LLM
              </small>
            </div>

            <div className="agent">
              MCP Gateway
              <small>
                Allow-listed tools
              </small>
            </div>

            <div className="agent">
              OpenTelemetry
              <small>
                Traces / metrics
              </small>
            </div>

            <div className="agent">
              Durable Queue
              <small>
                Retries / idempotency
              </small>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* =========================================================
   DASHBOARD APP
========================================================= */

function DashboardApp({
  user,
  onLogout,
}) {
  const [page, setPage] =
    useState("overview");

  const [caseId, setCaseId] =
    useState(null);

  const openCase = (id) => {
    setCaseId(id);
    setPage("case");
  };

  useEffect(() => {
    if (window.__openCase) {
      openCase(
        window.__openCase
      );

      delete window.__openCase;
    }
  }, [page]);

  let body;

  if (page === "overview") {
    body = (
      <Overview
        setPage={setPage}
        openCase={openCase}
        user={user}
      />
    );
  } else if (page === "cases") {
    body = (
      <Cases
        openCase={openCase}
        user={user}
      />
    );
  } else if (page === "customers") {
    body =
      user?.role === "CUSTOMER" ? (
        <CustomerProfile
          user={user}
          openCase={openCase}
        />
      ) : (
        <Customers
          setPage={setPage}
        />
      );
  } else if (page === "reviews") {
    body = (
      <ReviewQueue
        openCase={openCase}
      />
    );
  } else if (page === "users") {
    body = <AdminUsers />;
  } else if (page === "emails") {
    body = <EmailNotifications />;
  } else if (page === "monitor") {
    body = <AgentMonitoring />;
  } else if (
    page === "case" &&
    caseId
  ) {
    body = (
      <CaseDetail
        caseId={caseId}
        goBack={() =>
          setPage("cases")
        }
        user={user}
      />
    );
  } else {
    body = (
      <Overview
        setPage={setPage}
        openCase={openCase}
        user={user}
      />
    );
  }

  return (
    <Layout
      page={page}
      setPage={setPage}
      user={user}
      onLogout={onLogout}
    >
      {body}
    </Layout>
  );
}

/* =========================================================
   ROOT APP
========================================================= */

function App() {
  const [user, setUser] =
    useState(null);

  const [loading, setLoading] =
    useState(true);

  const logout = () => {
    localStorage.removeItem(
      "onboardai_token"
    );

    setUser(null);
  };

  useEffect(() => {
    const token =
      localStorage.getItem(
        "onboardai_token"
      );

    if (!token) {
      setLoading(false);
      return;
    }

    api("/api/auth/me")
      .then((data) => {
        if (!data) {
          throw new Error(
            "Authentication session returned an empty response."
          );
        }

        setUser(data);
      })
      .catch((error) => {
        console.error(
          "Session validation failed:",
          error
        );

        localStorage.removeItem(
          "onboardai_token"
        );

        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <Loading full />;
  }

  if (!user) {
    return (
      <AuthScreen
        onAuthenticated={setUser}
      />
    );
  }

  return (
    <DashboardApp
      user={user}
      onLogout={logout}
    />
  );
}

/* =========================================================
   MOUNT REACT
========================================================= */

const rootElement =
  document.getElementById("root");

if (!rootElement) {
  throw new Error(
    'OnboardAI: <div id="root"></div> was not found.'
  );
}

createRoot(rootElement).render(
  <App />
);