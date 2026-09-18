import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { LifeBuoy, ShoppingBag, X, Package } from "lucide-react";

export default function OrdersPage({ orders, cancelOrder }) {
  const navigate = useNavigate();
  const [selectedOrder, setSelectedOrder] = useState(null);

  const handleReportIssue = (order) => {
    const oid = String(order.order_id || order._id || "");
    navigate("/support", { state: { orderId: oid, order } });
  };

  return (
    <div className="container animate-fade">
      <h2>Your Orders</h2>
      <p style={{ color: "#6b7280", fontSize: "0.95rem", marginBottom: "20px" }}>
        Click any order card to view full details and raise support tickets.
      </p>

      {(!orders || orders.length === 0) ? (
        <div className="empty-tickets glass" style={{ textAlign: "center", padding: "40px" }}>
          <ShoppingBag size={40} color="#9ca3af" />
          <p style={{ marginTop: "12px", color: "#6b7280" }}>You have not placed any orders yet.</p>
        </div>
      ) : (
        <div className="orders-small-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: "20px" }}>
          {orders.slice().reverse().map((order) => {
            const oid = String(order.order_id || order._id || "");
            const firstItem = order.items?.[0] || {};
            const extraCount = (order.items?.length || 1) - 1;

            return (
              <div
                key={oid}
                className="order-card-compact glass"
                onClick={() => setSelectedOrder(order)}
                style={{
                  background: "white",
                  border: "1px solid #e5e7eb",
                  borderRadius: "12px",
                  padding: "16px",
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease"
                }}
              >
                <div style={{ position: "relative", width: "100%", height: "140px", borderRadius: "8px", overflow: "hidden", background: "#f3f4f6", marginBottom: "12px" }}>
                  <img
                    src={firstItem.image || "https://via.placeholder.com/150"}
                    alt={firstItem.name || "Product"}
                    style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  />
                  {extraCount > 0 && (
                    <span style={{ position: "absolute", bottom: "8px", right: "8px", background: "rgba(0,0,0,0.75)", color: "white", fontSize: "0.75rem", padding: "2px 8px", borderRadius: "12px", fontWeight: "600" }}>
                      +{extraCount} more
                    </span>
                  )}
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <span style={{ fontWeight: "700", fontSize: "1.1rem", color: "#111827" }}>
                    ₹{order.total}
                  </span>
                  <span className={`status-pill status-${order.status}`}>
                    {order.status}
                  </span>
                </div>

                <div style={{ fontSize: "0.85rem", color: "#6b7280", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                  {firstItem.name || "Order Items"}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {selectedOrder && (
        <div className="modal-overlay">
          <div className="ticket-modal-content glass animate-fade" style={{ maxWidth: "700px", width: "90%", maxHeight: "85vh", overflowY: "auto" }}>
            <div className="modal-header">
              <div>
                <h2>Order Details</h2>
                <span style={{ fontWeight: "700", color: "#2563eb", fontSize: "0.95rem" }}>
                  Order #{String(selectedOrder.order_id || selectedOrder._id || "")}
                </span>
              </div>
              <button className="close-btn" onClick={() => setSelectedOrder(null)}>
                <X size={20} />
              </button>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "16px", background: "#f9fafb", padding: "14px", borderRadius: "8px", marginBottom: "20px" }}>
              <div>
                <span style={{ fontSize: "0.8rem", color: "#6b7280", display: "block" }}>Status</span>
                <span className={`status-pill status-${selectedOrder.status}`} style={{ marginTop: "4px", display: "inline-block" }}>
                  {selectedOrder.status}
                </span>
              </div>
              <div>
                <span style={{ fontSize: "0.8rem", color: "#6b7280", display: "block" }}>Total Amount</span>
                <span style={{ fontWeight: "700", fontSize: "1.05rem", color: "#111827" }}>₹{selectedOrder.total}</span>
              </div>
              <div>
                <span style={{ fontSize: "0.8rem", color: "#6b7280", display: "block" }}>Shipping Cost</span>
                <span style={{ fontWeight: "600", color: "#374151" }}>₹{selectedOrder.shipping_cost || 0}</span>
              </div>
              <div>
                <span style={{ fontSize: "0.8rem", color: "#6b7280", display: "block" }}>Tax</span>
                <span style={{ fontWeight: "600", color: "#374151" }}>₹{selectedOrder.tax_cost || 0}</span>
              </div>
            </div>

            <h3 style={{ fontSize: "1.05rem", marginBottom: "12px", color: "#111827", display: "flex", alignItems: "center", gap: "6px" }}>
              <Package size={18} color="#2563eb" /> Ordered Products ({selectedOrder.items?.length || 0})
            </h3>

            <div className="order-items-list" style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "24px" }}>
              {selectedOrder.items?.map((item, idx) => (
                <div key={item.product_id || idx} style={{ display: "flex", alignItems: "center", gap: "14px", padding: "10px 14px", background: "#f3f4f6", borderRadius: "8px" }}>
                  <img src={item.image} alt={item.name} width="50" height="50" style={{ borderRadius: "6px", objectFit: "cover" }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: "600", color: "#1f2937" }}>{item.name}</div>
                    <div style={{ fontSize: "0.85rem", color: "#6b7280" }}>Qty: {item.qty} × ₹{item.price}</div>
                  </div>
                  <div style={{ fontWeight: "700", color: "#111827" }}>₹{item.price * item.qty}</div>
                </div>
              ))}
            </div>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", borderTop: "1px solid #e5e7eb", paddingTop: "16px" }}>
              {selectedOrder.status === "pending" && (
                <button
                  onClick={() => {
                    const oid = String(selectedOrder.order_id || selectedOrder._id || "");
                    cancelOrder(oid);
                    setSelectedOrder(null);
                  }}
                  style={{ background: "#ef4444", color: "white", padding: "10px 18px", borderRadius: "8px", fontWeight: "600" }}
                >
                  Cancel Order
                </button>
              )}
              <button
                onClick={() => {
                  handleReportIssue(selectedOrder);
                }}
                className="btn-primary"
                style={{ padding: "10px 20px" }}
              >
                <LifeBuoy size={16} /> Report Issue / Raise Ticket
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}