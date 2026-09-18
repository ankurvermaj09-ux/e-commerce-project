import { useState, useEffect } from "react";
import { useLocation } from "react-router-dom";
import api from "./api";
import { PlusCircle, X, Send, MessageSquare, Tag, Clock, AlertCircle, ShoppingBag, Info } from "lucide-react";

export default function TicketRaiser() {
  const location = useLocation();
  const [tickets, setTickets] = useState([]);
  const [userOrders, setUserOrders] = useState([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [replyMessage, setReplyMessage] = useState("");
  const [loadingModal, setLoadingModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [focusedOrder, setFocusedOrder] = useState(null);

  const [formData, setFormData] = useState({
    order_id: "",
    subject: "",
    category: "Order Issue",
    priority: "normal",
    description: ""
  });

  const loadTickets = async () => {
    try {
      const params = statusFilter ? { status: statusFilter } : {};
      const res = await api.get("/api/tickets", { params });
      setTickets(res.data || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadUserOrders = async () => {
    try {
      const res = await api.get("/api/orders");
      const ordersList = Array.isArray(res.data) ? res.data : (res.data?.orders || []);
      setUserOrders(ordersList);

      const passedState = location.state;
      if (passedState?.orderId) {
        const targetOid = String(passedState.orderId);
        setFormData(prev => ({ ...prev, order_id: targetOid }));
        setShowForm(true);
        if (passedState.order) {
          setFocusedOrder(passedState.order);
        }
      } else if (ordersList.length > 0 && !formData.order_id) {
        setFormData(prev => ({ ...prev, order_id: String(ordersList[0].order_id || ordersList[0]._id || "") }));
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadTickets();
    loadUserOrders();
  }, [statusFilter, location.state]);

  const handleOrderChange = (e) => {
    const selectedOid = e.target.value;
    setFormData({ ...formData, order_id: selectedOid });
    const found = userOrders.find(o => String(o.order_id || o._id || "") === selectedOid);
    setFocusedOrder(found || null);
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!formData.order_id || !formData.order_id.trim()) {
      alert("Please select an Order ID to link to your ticket.");
      return;
    }
    if (!formData.subject.trim() || !formData.description.trim()) return;

    setSubmitting(true);
    try {
      await api.post("/api/tickets", {
        order_id: formData.order_id.trim(),
        subject: formData.subject.trim(),
        category: formData.category,
        priority: formData.priority,
        description: formData.description.trim()
      });
      setFormData({
        order_id: userOrders.length > 0 ? String(userOrders[0].order_id || userOrders[0]._id || "") : "",
        subject: "",
        category: "Order Issue",
        priority: "normal",
        description: ""
      });
      setShowForm(false);
      setFocusedOrder(null);
      loadTickets();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to create ticket");
    } finally {
      setSubmitting(false);
    }
  };

  const openTicketModal = async (ticketId) => {
    setLoadingModal(true);
    try {
      const res = await api.get(`/api/tickets/${ticketId}`);
      setSelectedTicket(res.data);
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to load ticket history");
    } finally {
      setLoadingModal(false);
    }
  };

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyMessage.trim() || !selectedTicket) return;

    try {
      const res = await api.post(`/api/tickets/${selectedTicket.ticket_id}/messages`, {
        message: replyMessage.trim()
      });
      setSelectedTicket(res.data);
      setReplyMessage("");
      loadTickets();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to send message");
    }
  };

  return (
    <div className="container animate-fade">
      <div className="ticket-header-bar">
        <div>
          <h2>Order Support & Complaints</h2>
          <p className="subtitle-text">Raise issues linked to your placed orders and track resolution</p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowForm(!showForm)}
        >
          <PlusCircle size={18} /> {showForm ? "Cancel" : "Raise a Ticket"}
        </button>
      </div>

      {showForm && (
        <div className="ticket-form-card glass animate-fade">
          <h3>Submit an Order Complaint / Ticket</h3>

          {focusedOrder && (
            <div className="focused-order-banner" style={{ background: "#eff6ff", border: "1px solid #bfdbfe", padding: "14px", borderRadius: "8px", marginBottom: "16px", fontSize: "0.9rem" }}>
              <div style={{ fontWeight: "700", color: "#1e40af", display: "flex", alignItems: "center", gap: "6px" }}>
                <Info size={16} /> Order Details: Order #{String(focusedOrder.order_id || focusedOrder._id || "")} (Total: ₹{focusedOrder.total}) - Status: {focusedOrder.status}
              </div>
              <div style={{ color: "#4b5563", marginTop: "4px" }}>
                Items: {focusedOrder.items?.map(i => `${i.name} (x${i.qty})`).join(", ")}
              </div>
            </div>
          )}

          <form onSubmit={handleCreateTicket}>
            <div className="form-row">
              <div className="form-group">
                <label>Select Order *</label>
                {userOrders.length > 0 ? (
                  <select
                    value={formData.order_id}
                    onChange={handleOrderChange}
                    required
                  >
                    <option value="">-- Choose an Order --</option>
                    {userOrders.map((o) => {
                      const oid = String(o.order_id || o._id || "");
                      const itemSummary = o.items?.map(i => i.name).slice(0, 2).join(", ") || "";
                      return (
                        <option key={oid} value={oid}>
                          Order #{oid.slice(0, 10)}... (₹{o.total}) - {itemSummary} [{o.status}]
                        </option>
                      );
                    })}
                  </select>
                ) : (
                  <input
                    type="text"
                    placeholder="Enter Order ID"
                    value={formData.order_id}
                    onChange={(e) => setFormData({ ...formData, order_id: e.target.value })}
                    required
                  />
                )}
              </div>

              <div className="form-group">
                <label>Problem Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <option value="Order Issue">Order Issue</option>
                  <option value="Product Issue">Product Issue</option>
                  <option value="Delivery Issue">Delivery Issue</option>
                  <option value="Refund Request">Refund Request</option>
                  <option value="Return Request">Return Request</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="form-group">
                <label>Priority</label>
                <select
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                >
                  <option value="low">Low</option>
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>Subject</label>
              <input
                type="text"
                placeholder="Brief summary of the issue with this order"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>Detailed Description</label>
              <textarea
                rows="4"
                placeholder="Describe your product/order issue, delivery problem, or refund/return request..."
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                required
              />
            </div>

            <button type="submit" className="btn-submit" disabled={submitting}>
              {submitting ? "Submitting Ticket..." : "Submit Ticket"}
            </button>
          </form>
        </div>
      )}

      <div className="ticket-filter-bar">
        <label>Filter by Status:</label>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Tickets</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div className="tickets-grid">
        {tickets.length === 0 ? (
          <div className="empty-tickets glass">
            <MessageSquare size={40} color="#9ca3af" />
            <p>No support tickets found for your orders.</p>
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
              <p className="ticket-order-ref" style={{ fontWeight: 600, color: "#2563eb", marginBottom: "8px" }}>
                <ShoppingBag size={14} style={{ display: "inline", marginRight: "4px" }} /> Linked Order: #{t.order_id}
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
                <h2>Ticket #{selectedTicket.ticket_id.slice(0, 8)}... - {selectedTicket.subject}</h2>
                <div className="modal-sub-info">
                  <span className={`status-pill status-${selectedTicket.status}`}>
                    {selectedTicket.status.replace("_", " ")}
                  </span>
                  <span>Order: #{selectedTicket.order_id}</span>
                  <span>Category: {selectedTicket.category}</span>
                  <span>Priority: {selectedTicket.priority}</span>
                </div>
              </div>
              <button className="close-btn" onClick={() => setSelectedTicket(null)}>
                <X size={20} />
              </button>
            </div>

            <div className="thread-history">
              {selectedTicket.history?.map((entry, index) => (
                <div
                  key={index}
                  className={`history-item history-${entry.action} actor-${entry.actor}`}
                >
                  <div className="history-meta">
                    <span className="history-actor">
                      {entry.actor === "admin" ? "Support Admin" : "You"} ({entry.actor_email})
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

            {selectedTicket.status !== "closed" ? (
              <form onSubmit={handleSendReply} className="reply-form">
                <textarea
                  rows="3"
                  placeholder="Type your reply..."
                  value={replyMessage}
                  onChange={(e) => setReplyMessage(e.target.value)}
                  required
                />
                <button type="submit" className="btn-reply">
                  <Send size={16} /> Reply
                </button>
              </form>
            ) : (
              <div className="ticket-closed-msg">
                This ticket is closed. Reply to reopen or submit a new ticket.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}