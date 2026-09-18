import { useNavigate } from "react-router-dom";

export default function Aboutus() {
  const navigate = useNavigate();

  return (
    <div className="landing-container">

      {/* Project Overview */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>About This Project</h1>
          <p>
            A production-oriented full-stack e-commerce platform designed
            with scalable architecture, secure application design,
            automated deployment, and reliable cloud infrastructure in mind.
            <br /><br />
            The platform combines a complete e-commerce experience with
            production-grade practices for deploying, scaling, monitoring,
            and maintaining the application.
          </p>
        </div>
      </section>


      {/* Project Vision */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>The Vision Behind This Project</h1>
          <p>
            The goal is to build an e-commerce platform that goes beyond
            application functionality and reflects how modern production
            systems are designed and operated.
            <br /><br />
            The platform is designed around reliability, scalability,
            automation, security, and maintainability while providing a
            complete shopping and administration experience.
          </p>
        </div>
      </section>


      {/* Technology Stack */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Technology Stack</h1>

          <p>
            <strong>Frontend:</strong><br />
            React (Vite)<br />
            Framer Motion<br />
            Axios<br />
            React Router
          </p>

          <p>
            <strong>Backend:</strong><br />
            FastAPI<br />
            Python<br />
            JWT Authentication<br />
            Role-Based Access Control
          </p>

          <p>
            <strong>Database:</strong><br />
            MongoDB
          </p>

          <p>
            <strong>Infrastructure & DevOps:</strong><br />
            Docker<br />
            Docker Compose<br />
            GitHub Actions<br />
            AWS<br />
            Infrastructure as Code<br />
            Load Balancing<br />
            Application Monitoring
          </p>
        </div>
      </section>


      {/* Application Features */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Application Features</h1>

          <p>
            User Authentication (JWT-based)<br />
            Role-Based Access (Admin / User separation)<br />
            Product Browsing & Management<br />
            Wishlist & Cart System<br />
            Secure Checkout Flow<br />
            Order Management<br />
            Order Status Tracking<br />
            Inventory Management<br />
            Session Expiry Handling<br />
            Business Analytics
          </p>
        </div>
      </section>


      {/* Admin Capabilities */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Admin & Business Capabilities</h1>

          <p>
            The administrative interface provides operational visibility
            into the platform and its business activity.
          </p>

          <p>
            Revenue analytics<br />
            Category-wise sales breakdown<br />
            Cancellation ratio<br />
            Best-selling products<br />
            Top customer analysis<br />
            Inventory monitoring<br />
            Order management<br />
            CSV export functionality
          </p>
        </div>
      </section>


      {/* Infrastructure */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Cloud Infrastructure</h1>

          <p>
            The application is designed to run on cloud infrastructure with
            a focus on reliability, controlled access, scalability, and
            efficient resource utilization.
          </p>

          <p>
            Virtual networking and subnet isolation<br />
            Application servers<br />
            Load balancing<br />
            Scalable compute resources<br />
            Secure network access<br />
            Cloud-based storage<br />
            Environment-specific configuration
          </p>
        </div>
      </section>


      {/* CI/CD */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Automated CI/CD</h1>

          <p>
            Application delivery is automated through a continuous
            integration and deployment pipeline.
            <br /><br />
            Code changes are validated, packaged, and prepared for
            deployment through an automated workflow, reducing manual
            deployment steps and providing a consistent release process.
          </p>

          <p>
            Source Control → Build → Test → Containerize → Deploy
          </p>
        </div>
      </section>


      {/* Scalability */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Scalability & High Availability</h1>

          <p>
            The infrastructure is designed so that application traffic can
            be distributed across multiple application instances instead
            of depending on a single server.
            <br /><br />
            Health checks and load balancing help maintain application
            availability while allowing compute resources to scale with
            changing workloads.
          </p>

          <p>
            Load Balancing<br />
            Health Checks<br />
            Horizontal Scaling<br />
            Fault Isolation<br />
            Resource-based Scaling
          </p>
        </div>
      </section>


      {/* Security */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Security</h1>

          <p>
            Security is incorporated across both the application and
            infrastructure layers.
          </p>

          <p>
            JWT-based authentication<br />
            Role-Based Access Control<br />
            Secure API access<br />
            IAM-based infrastructure access<br />
            Network security controls<br />
            HTTPS communication<br />
            Protected application secrets<br />
            Environment-based configuration
          </p>
        </div>
      </section>


      {/* Monitoring */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Monitoring & Observability</h1>

          <p>
            The platform is designed with operational visibility in mind,
            allowing infrastructure and application health to be monitored
            after deployment.
          </p>

          <p>
            Infrastructure metrics<br />
            Application health monitoring<br />
            Resource utilization<br />
            Application logs<br />
            Error tracking<br />
            Service health checks
          </p>
        </div>
      </section>


      {/* Reliability */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Reliability & Recovery</h1>

          <p>
            Production systems must be capable of handling failures and
            recovering from unexpected events.
            <br /><br />
            The platform incorporates backup, recovery, health monitoring,
            and failure-handling practices to improve system reliability
            and reduce operational risk.
          </p>
        </div>
      </section>


      {/* Engineering Principles */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Engineering Principles</h1>

          <p>
            Automation over manual operations<br />
            Infrastructure as Code<br />
            Reproducible deployments<br />
            Secure configuration management<br />
            Horizontal scalability<br />
            Continuous monitoring<br />
            Fault tolerance<br />
            Reliable recovery
          </p>
        </div>
      </section>


      {/* Why This Project Matters */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Why This Project Matters</h1>

          <p>
            This project demonstrates how a real application can be
            engineered beyond the development environment and operated as
            a production-oriented system.
            <br /><br />
            It brings together application development, cloud infrastructure,
            automation, deployment, scalability, security, monitoring, and
            reliability into a single platform.
          </p>
        </div>
      </section>


      {/* Explore */}
      <section className="hero-section">
        <div className="hero-left">
          <h1>Explore the Platform</h1>

          <p>
            Explore the e-commerce platform and experience the application
            functionality built on top of its production-oriented
            infrastructure.
          </p>

          <button onClick={() => navigate("/shop")}>
            View Store
          </button>
        </div>
      </section>

    </div>
  );
}
