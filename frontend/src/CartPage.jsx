import { Plus, Minus, CreditCard } from "lucide-react";

export default function CartPage({ cart, checkout, increaseQty, decreaseQty, formData, setFormData }) {
  return (
    <div>
      <h2>Checkout Details</h2>
      <div className="cart-container">
        <h2>Cart</h2>
        <div className="cart-list">
          {cart.length === 0 ? (
            <p>Empty</p>
          ) : (
            <div className="cart-card">
              {cart.map((item) => (
                <div className="cart-item" key={item.product_id}>
                  <img src={item.image} alt={item.name} width="40" />
                  <span>{item.name}</span>
                  <span>x {item.qty}</span>
                  <button type="button" onClick={() => decreaseQty(item.product_id)}><Minus size={16} /></button>
                  <button type="button" onClick={() => increaseQty(item.product_id)}><Plus size={16} /></button>
                </div>
              ))}
              <div style={{ marginTop: "20px" }}>
                {setFormData && formData && (
                  <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginBottom: "15px" }}>
                    <input
                      type="text"
                      placeholder="Shipping Address"
                      value={formData.shipping_address || ""}
                      onChange={(e) => setFormData({ ...formData, shipping_address: e.target.value })}
                      style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
                    />
                    <select
                      value={formData.payment_method || ""}
                      onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                      style={{ padding: "8px", borderRadius: "4px", border: "1px solid #ccc" }}
                    >
                      <option value="">Select Payment Method</option>
                      <option value="credit_card">Credit Card</option>
                      <option value="paypal">PayPal</option>
                      <option value="cod">Cash on Delivery</option>
                    </select>
                  </div>
                )}
                <button onClick={checkout}><CreditCard size={18} /> Checkout</button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}