import { useState, useEffect } from "react";
import api from "./api";
import { Search, X, Send, Tag, Clock, AlertCircle, User } from "lucide-react";

export default function AdminTickets() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({ total: 0, open: 0, in_progress: 0, resolved: 0, closed: 0 });
  const [statusFilter, setStatusFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [replyMessage, setReplyMessage] = useState("");
  const [statusNote, setStatusNote] = useState("");
  const [typingTimeout, setTypingTimeout] = useState(null);

  const loadStats = async () => {
    try {
      const res = await api.get("/api/admin/tickets/stats");
      setStats(res.data || { total: 0, open: 0, in_progress: 0, resolved: 0, closed: 0 });
    } catch (err) {
      console.error(err);
    }
  };

  const loadTickets = async (filter = statusFilter, query = searchQuery) => {
    try {
      const params = {};
      if (filter) params.status = filter;
      if (query.trim()) params.q = query.trim();
      const res = await api.get("/api/admin/tickets", { params });
      setTickets(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadStats();
    loadTickets();
  }, [statusFilter]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchQuery(val);
    if (typingTimeout) clearTimeout(typingTimeout);
    const timeout = setTimeout(() => {
      loadTickets(statusFilter, val);
    }, 400);
    setTypingTimeout(timeout);
  };

  const openTicketModal = async (ticketId) => {
    try {
      const res = await api.get(`/api/admin/tickets/${ticketId}`);
      setSelectedTicket(res.data);
      setStatusNote("");
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to load ticket");
    }
  };

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyMessage.trim() || !selectedTicket) return;

    try {
      const res = await api.post(`/api/admin/tickets/${selectedTicket.ticket_id}/messages`, {
        message: replyMessage.trim()
      });
      setSelectedTicket(res.data);
      setReplyMessage("");
      loadStats();
      loadTickets();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to send message");
    }
  };

  const handleStatusChange = async (newStatus) => {
    if (!selectedTicket || selectedTicket.status === newStatus) return;

    try {
      const res = await api.put(`/api/admin/tickets/${selectedTicket.ticket_id}/status`, {
        status: newStatus,
        note: statusNote.trim() || null
      });
      setSelectedTicket(res.data);
      setStatusNote("");
      loadStats();
      loadTickets();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update status");
    }
  };

  return (
    <div className="admin-tickets-container animate-fade">
      <div className="admin-ticket-stats-bar">
        <div className="admin-stat-chip">
          <span className="stat-num">{stats.total}</span>
          <span className="stat-label">Total</span>
        </div>
        <div className="admin-stat-chip chip-open">
          <span className="stat-num">{stats.open}</span>
          <span className="stat-label">Open</span>
        </div>
        <div className="admin-stat-chip chip-progress">
          <span className="stat-num">{stats.in_progress}</span>
          <span className="stat-label">In Progress</span>
        </div>
        <div className="admin-stat-chip chip-resolved">
          <span className="stat-num">{stats.resolved}</span>
          <span className="stat-label">Resolved</span>
        </div>
        <div className="admin-stat-chip chip-closed">
          <span className="stat-num">{stats.closed}</span>
          <span className="stat-label">Closed</span>
        </div>
      </div>

      <div className="admin-ticket-controls">
        <div className="search-bar">
          <Search className="search-icon-inner" size={18} />
          <input
            type="text"
            placeholder="Search subject or email..."
            value={searchQuery}
            onChange={handleSearchChange}
          />
          {searchQuery && (
            <X
              className="clear-search"
              size={18}
              onClick={() => {
                setSearchQuery("");
                loadTickets(statusFilter, "");
              }}
            />
          )}
        </div>

        <div className="filter-group">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      <div className="admin-tickets-grid">
        {tickets.length === 0 ? (
          <div className="empty-tickets glass">
            <p>No support tickets match the current filters.</p>
          </div>
        ) : (
          tickets.map((t) => (
            <div
              key={t.ticket_id}
              className="ticket-card glass"
              onClick={() => openTicketModal(t.ticket_id)}
            >
              <div className="ticket-card-top">
                <span className="ticket-id">#{t.ticket_id.slice(0, 8)}...</span>
                <span className={`status-pill status-${t.status}`}>
                  {t.status.replace("_", " ")}
                </span>
              </div>
              <h3 className="ticket-subject">{t.subject}</h3>
              <p className="ticket-user-email">
                <User size={14} /> {t.user_email}
              </p>
              <p className="ticket-order-ref" style={{ fontWeight: 600, color: "#2563eb", marginBottom: "8px" }}>
                Order ID: #{t.order_id}
              </p>
              <div className="ticket-tags">
                <span className="tag-item"><Tag size={14} /> {t.category}</span>
                <span className={`priority-tag priority-${t.priority}`}>
                  <AlertCircle size={14} /> {t.priority}
                </span>
              </div>
              <div className="ticket-card-bottom">
                <span className="ticket-time">
                  <Clock size={14} /> Updated: {new Date(t.updated_at).toLocaleString("en-IN")}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {selectedTicket && (
        <div className="modal-overlay">
          <div className="ticket-modal-content glass animate-fade">
            <div className="modal-header">
              <div>
                <h2>#{selectedTicket.ticket_id} - {selectedTicket.subject}</h2>
                <div className="modal-sub-info">
                  <span className={`status-pill status-${selectedTicket.status}`}>
                    {selectedTicket.status.replace("_", " ")}
                  </span>
                  <span>User: {selectedTicket.user_email}</span>
                  <span>Category: {selectedTicket.category}</span>
                  <span>Priority: {selectedTicket.priority}</span>
                  {selectedTicket.order_id && <span>Order: #{selectedTicket.order_id}</span>}
                </div>
              </div>
              <button className="close-btn" onClick={() => setSelectedTicket(null)}>
                <X size={20} />
              </button>
            </div>

            <div className="admin-status-controls">
              <span className="controls-label">Change Status:</span>
              <div className="status-btn-group">
                <button
                  className="status-action-btn btn-status-open"
                  disabled={selectedTicket.status === "open"}
                  onClick={() => handleStatusChange("open")}
                >
                  Open
                </button>
                <button
                  className="status-action-btn btn-status-progress"
                  disabled={selectedTicket.status === "in_progress"}
                  onClick={() => handleStatusChange("in_progress")}
                >
                  In Progress
                </button>
                <button
                  className="status-action-btn btn-status-resolved"
                  disabled={selectedTicket.status === "resolved"}
                  onClick={() => handleStatusChange("resolved")}
                >
                  Resolved
                </button>
                <button
                  className="status-action-btn btn-status-closed"
                  disabled={selectedTicket.status === "closed"}
                  onClick={() => handleStatusChange("closed")}
                >
                  Closed
                </button>
              </div>
              <input
                type="text"
                placeholder="Optional status change note..."
                className="status-note-input"
                value={statusNote}
                onChange={(e) => setStatusNote(e.target.value)}
              />
            </div>

            <div className="thread-history">
              {selectedTicket.history?.map((entry, index) => (
                <div
                  key={index}
                  className={`history-item history-${entry.action} actor-${entry.actor}`}
                >
                  <div className="history-meta">
                    <span className="history-actor">
                      {entry.actor === "admin" ? "Support Admin" : "User"} ({entry.actor_email})
                    </span>
                    <span className="history-time">
                      {new Date(entry.timestamp).toLocaleString("en-IN")}
                    </span>
                  </div>
                  {entry.action === "status_change" ? (
                    <div className="status-change-notice">
                      Status changed to <strong className={`status-${entry.status}`}>{entry.status}</strong>
                      {entry.message ? `: ${entry.message}` : ""}
                    </div>
                  ) : (
                    <p className="history-message">{entry.message}</p>
                  )}
                </div>
              ))}
            </div>

            <form onSubmit={handleSendReply} className="reply-form">
              <textarea
                rows="3"
                placeholder="Type admin response..."
                value={replyMessage}
                onChange={(e) => setReplyMessage(e.target.value)}
                required
              />
              <button type="submit" className="btn-reply">
                <Send size={16} /> Reply to User
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
