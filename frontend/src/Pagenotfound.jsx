import { Link } from "react-router-dom";
import { ArrowLeft, Compass } from "lucide-react";

export default function Pagenotfound() {
    return (
        <div className="container animate-fade" style={{ minHeight: "70vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <div className="glass" style={{ maxWidth: "600px", width: "100%", padding: "40px", borderRadius: "16px", textAlign: "center" }}>
                <div style={{ display: "inline-flex", padding: "16px", borderRadius: "50%", background: "#eff6ff", color: "#2563eb", marginBottom: "20px" }}>
                    <Compass size={48} />
                </div>
                <h1 style={{ fontSize: "4rem", fontWeight: "800", color: "#2563eb", marginBottom: "8px", lineHeight: "1" }}>
                    404
                </h1>
                <h2 style={{ fontSize: "1.5rem", fontWeight: "600", color: "#1f2937", marginBottom: "12px" }}>
                    Page Not Found
                </h2>
                <p style={{ color: "#6b7280", fontSize: "1rem", lineHeight: "1.6", marginBottom: "28px" }}>
                    Not all those who wander are lost, but you are, this URL doesn't exist.
                </p>
                <Link
                    to="/"
                    className="btn-primary"
                    style={{ display: "inline-flex", alignItems: "center", gap: "8px", textDecoration: "none" }}
                >
                    <ArrowLeft size={18} /> Take me to home
                </Link>
            </div>
        </div>
    );
}