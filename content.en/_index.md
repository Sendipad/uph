---
title: "Unified Party Hub"
layout: landing
---

<!-- Hero Section -->
<div class="book-hero" style="text-align:center; padding: 4rem 0; background: linear-gradient(to bottom right, #0f172a, #1e293b, #0f172a);">
  <div class="hero-logo" style="margin-bottom: 2rem; animation: float 3s ease-in-out infinite;">
    <img src="/uph-logo.png" alt="UPH Logo" style="width: 120px; height: 120px; border-radius: 24px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);"/>
  </div>
  
  <div class="hero-badge" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.5rem 1rem; background: rgba(37, 99, 235, 0.1); border: 1px solid rgba(37, 99, 235, 0.3); border-radius: 50px; color: #06b6d4; font-size: 0.875rem; font-weight: 500; margin-bottom: 1.5rem;">
    ✨ Version 2.7 Now Available
  </div>
  
  <h1 style="font-size: clamp(2.5rem, 5vw, 4rem); font-weight: 800; line-height: 1.1; margin-bottom: 1.5rem; background: linear-gradient(135deg, #ffffff 0%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
    Unified Party Hub
  </h1>
  <p style="font-size: clamp(1.25rem, 3vw, 1.75rem); color: #94a3b8; margin-bottom: 1rem; font-weight: 300;">
    Master Data Management for ERPNext
  </p>
  <p style="font-size: 1.125rem; color: #64748b; max-width: 700px; margin: 0 auto 2.5rem;">
    Centralize your customer, supplier, and employee data with intelligent hierarchy management, multi-currency support, and enterprise-grade governance.
  </p>
  
  <div style="margin: 2rem 0; display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
    <a href="./docs/introduction/" class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 1rem 2rem; font-size: 1rem; font-weight: 600; border-radius: 12px; border: none; cursor: pointer; text-decoration: none; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); color: white; box-shadow: 0 4px 14px 0 rgba(37, 99, 235, 0.4);">
      <i class="fas fa-rocket"></i> Get Started
    </a>
    <a href="./docs/features/" class="btn btn-secondary" style="display: inline-flex; align-items: center; gap: 0.5rem; padding: 1rem 2rem; font-size: 1rem; font-weight: 600; border-radius: 12px; border: 2px solid rgba(255, 255, 255, 0.2); cursor: pointer; text-decoration: none; background: transparent; color: white;">
      <i class="fas fa-book"></i> Documentation
    </a>
  </div>

  <!-- Stats -->
  <div style="display: flex; justify-content: center; gap: 3rem; flex-wrap: wrap; margin-top: 3rem;">
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700; color: white;">10K+</div>
      <div style="font-size: 0.875rem; color: #64748b;">Organizations</div>
    </div>
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700; color: white;">50M+</div>
      <div style="font-size: 0.875rem; color: #64748b;">Parties Managed</div>
    </div>
    <div style="text-align: center;">
      <div style="font-size: 2rem; font-weight: 700; color: white;">99.9%</div>
      <div style="font-size: 0.875rem; color: #64748b;">Uptime SLA</div>
    </div>
  </div>

  <div style="margin-top: 2rem; display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap;">
    <a href="https://github.com/Sendipad/uph/releases"><img src="https://img.shields.io/github/v/release/Sendipad/uph?style=for-the-badge" alt="Latest Release"/></a>
    <a href="https://github.com/Sendipad/uph/actions/workflows/test_v15.yml"><img src="https://img.shields.io/badge/Frappe%20%2F%20ERPNext-v15+-red?style=for-the-badge" alt="Supports ERPNext v15+"/></a>
    <a href="https://github.com/Sendipad/uph"><img src="https://img.shields.io/badge/Localization-Arabic%20(100%25)-green?style=for-the-badge" alt="Arabic 100%"/></a>
  </div>
</div>

<!-- Key Features Section -->
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 1rem;">
  <h2 style="text-align: center; font-size: clamp(2rem, 4vw, 2.5rem); font-weight: 700; color: white; margin-bottom: 0.5rem;">
    🚀 Powerful Features
  </h2>
  <p style="text-align: center; font-size: 1.125rem; color: #64748b; margin-bottom: 3rem;">
    Everything you need to master your party data in ERPNext
  </p>

  <!-- Features Grid -->
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 2rem;">
    
    <!-- Feature 1: Tree Hierarchy -->
    <div class="feature-card" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;">
      <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); border-radius: 12px; margin-bottom: 1.5rem;">
        <svg style="width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">🌳 Tree Hierarchy</h3>
      <p style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">Organize parties in intelligent hierarchical structures with automatic parent-child relationships and cascading updates.</p>
    </div>
    
    <!-- Feature 2: Multi-Role Linking -->
    <div class="feature-card" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;">
      <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%); border-radius: 12px; margin-bottom: 1.5rem;">
        <svg style="width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">🔗 Multi-Role Linking</h3>
      <p style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">Link customers to suppliers, connect employees to multiple organizations, and manage complex relationship networks.</p>
    </div>
    
    <!-- Feature 3: Multi-Currency Support -->
    <div class="feature-card" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;">
      <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%); border-radius: 12px; margin-bottom: 1.5rem;">
        <svg style="width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M2 12h20"/>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">💱 Multi-Currency Support</h3>
      <p style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">Manage party balances and transactions across 150+ currencies with real-time exchange rates and hierarchical account mapping.</p>
    </div>
    
    <!-- Feature 4: Analytics & Reporting -->
    <div class="feature-card" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;">
      <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); border-radius: 12px; margin-bottom: 1.5rem;">
        <svg style="width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 20V10"/>
          <path d="M12 20V4"/>
          <path d="M6 20v-6"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">📊 Analytics & Reporting</h3>
      <p style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">Gain insights with built-in dashboards, financial reports, aging analysis, and customizable KPI widgets.</p>
    </div>
    
    <!-- Feature 5: Data Governance -->
    <div class="feature-card" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;">
      <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #06b6d4 0%, #2563eb 100%); border-radius: 12px; margin-bottom: 1.5rem;">
        <svg style="width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          <path d="M9 12l2 2 4-4"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">🛡️ Data Governance</h3>
      <p style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">Ensure data quality with validation rules, audit trails, compliance reporting, and role-based access controls.</p>
    </div>
    
    <!-- Feature 6: SmartCache Performance -->
    <div class="feature-card" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;">
      <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #ef4444 0%, #f59e0b 100%); border-radius: 12px; margin-bottom: 1.5rem;">
        <svg style="width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">⚡ SmartCache Performance</h3>
      <p style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">Experience lightning-fast performance with intelligent caching, background sync, and optimized database queries.</p>
    </div>
    
    <!-- Feature 7: Duplicate Detection -->
    <div class="feature-card" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;">
      <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%); border-radius: 12px; margin-bottom: 1.5rem;">
        <svg style="width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="M21 21l-4.35-4.35"/>
          <path d="M11 8a3 3 0 0 0 0 6"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">🔍 Duplicate Detection</h3>
      <p style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">Identify and merge duplicate parties using fuzzy matching algorithms, customizable rules, and batch processing.</p>
    </div>
    
    <!-- Feature 8: Multi-Language Support -->
    <div class="feature-card" style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;">
      <div style="width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #10b981 0%, #2563eb 100%); border-radius: 12px; margin-bottom: 1.5rem;">
        <svg style="width: 32px; height: 32px; fill: white;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"/>
          <path d="M2 12h20"/>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
      </div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">🌍 Multi-Language Support</h3>
      <p style="font-size: 0.95rem; color: #64748b; line-height: 1.7;">Full RTL support for Arabic and 20+ languages with translated interfaces, localized formats, and Unicode compliance.</p>
    </div>
    
  </div>
</div>

<!-- Problem Solution Section -->
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 1rem;">
  <h2 style="text-align: center; font-size: clamp(2rem, 4vw, 2.5rem); font-weight: 700; color: white; margin-bottom: 0.5rem;">
    💡 Why UPH?
  </h2>
  <p style="text-align: center; font-size: 1.125rem; color: #64748b; margin-bottom: 3rem;">
    Standard ERPNext has limitations. UPH solves them.
  </p>

  <!-- Problem Cards -->
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 3rem;">
    
    <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 12px; padding: 1.5rem;">
      <div style="font-size: 2rem; margin-bottom: 1rem;">⚠️</div>
      <h3 style="font-size: 1.125rem; font-weight: 600; color: #ef4444; margin-bottom: 0.5rem;">Fragmented Identity</h3>
      <p style="font-size: 0.95rem; color: #94a3b8;">A single legal entity acting as both Customer and Supplier exists as two disconnected documents.</p>
    </div>
    
    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 12px; padding: 1.5rem;">
      <div style="font-size: 2rem; margin-bottom: 1rem;">💱</div>
      <h3 style="font-size: 1.125rem; font-weight: 600; color: #f59e0b; margin-bottom: 0.5rem;">Multi-Currency Complexity</h3>
      <p style="font-size: 0.95rem; color: #94a3b8;">Transacting in multiple currencies often requires duplicate party records (e.g., "Customer USD", "Customer EUR").</p>
    </div>
    
    <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 1.5rem;">
      <div style="font-size: 2rem; margin-bottom: 1rem;">📊</div>
      <h3 style="font-size: 1.125rem; font-weight: 600; color: #3b82f6; margin-bottom: 0.5rem;">Siloed Reporting</h3>
      <p style="font-size: 0.95rem; color: #94a3b8;">Financial reports are segmented by specific Party records, making 360-degree visibility difficult.</p>
    </div>
    
    <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px; padding: 1.5rem;">
      <div style="font-size: 2rem; margin-bottom: 1rem;">🔄</div>
      <h3 style="font-size: 1.125rem; font-weight: 600; color: #a855f7; margin-bottom: 0.5rem;">Data Redundancy</h3>
      <p style="font-size: 0.95rem; color: #94a3b8;">Address and Contact data must be duplicated across multiple party roles.</p>
    </div>
    
  </div>

  <!-- Solution Summary -->
  <div style="background: linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%); border: 1px solid rgba(37, 99, 235, 0.3); border-radius: 16px; padding: 2.5rem; text-align: center;">
    <h3 style="font-size: 1.5rem; font-weight: 700; color: white; margin-bottom: 1rem;">UPH Solves These Problems</h3>
    <p style="font-size: 1.1rem; color: #94a3b8; max-width: 800px; margin: 0 auto;">
      By treating the <strong style="color: #06b6d4;">"Party"</strong> as a single legal entity and <strong style="color: #06b6d4;">"Roles"</strong> (Customer, Supplier) as attributes, UPH delivers:
    </p>
    <div style="display: flex; justify-content: center; gap: 2rem; flex-wrap: wrap; margin-top: 1.5rem;">
      <div style="display: flex; align-items: center; gap: 0.5rem; color: #10b981;">
        <svg style="width: 20px; height: 20px; fill: #10b981;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 12l2 2 4-4"/>
          <circle cx="12" cy="12" r="10"/>
        </svg>
        <span>True Multi-Currency Support</span>
      </div>
      <div style="display: flex; align-items: center; gap: 0.5rem; color: #10b981;">
        <svg style="width: 20px; height: 20px; fill: #10b981;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 12l2 2 4-4"/>
          <circle cx="12" cy="12" r="10"/>
        </svg>
        <span>Unified Analytic Accounting</span>
      </div>
      <div style="display: flex; align-items: center; gap: 0.5rem; color: #10b981;">
        <svg style="width: 20px; height: 20px; fill: #10b981;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M9 12l2 2 4-4"/>
          <circle cx="12" cy="12" r="10"/>
        </svg>
        <span>360-Degree Visibility</span>
      </div>
    </div>
  </div>
</div>

<!-- Core DocTypes Section -->
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 1rem;">
  <h2 style="text-align: center; font-size: clamp(2rem, 4vw, 2.5rem); font-weight: 700; color: white; margin-bottom: 0.5rem;">
    📦 Core DocTypes
  </h2>
  <p style="text-align: center; font-size: 1.125rem; color: #64748b; margin-bottom: 3rem;">
    Powerful data structures for comprehensive party management
  </p>

  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem;">
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <div style="font-size: 1.5rem; margin-bottom: 0.75rem;">🎯</div>
      <h4 style="font-size: 1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Party Master</h4>
      <p style="font-size: 0.875rem; color: #64748b;">Central hub with tree-based hierarchy, multi-role support, and consolidated visibility.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <div style="font-size: 1.5rem; margin-bottom: 0.75rem;">📊</div>
      <h4 style="font-size: 1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Party Analytic Accounting</h4>
      <p style="font-size: 0.875rem; color: #64748b;">Oracle TCA-like site accounting with multiple dimension types.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <div style="font-size: 1.5rem; margin-bottom: 0.75rem;">🔗</div>
      <h4 style="font-size: 1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Party Master Parties</h4>
      <p style="font-size: 0.875rem; color: #64748b;">Junction table linking Party Master to Customers, Suppliers, Employees.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <div style="font-size: 1.5rem; margin-bottom: 0.75rem;">⚙️</div>
      <h4 style="font-size: 1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Party Master Settings</h4>
      <p style="font-size: 0.875rem; color: #64748b;">Central configuration for rules, field mapping, and PAA settings.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <div style="font-size: 1.5rem; margin-bottom: 0.75rem;">🤝</div>
      <h4 style="font-size: 1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Party Relationship</h4>
      <p style="font-size: 0.875rem; color: #64748b;">Define N-to-N relationships between parties with ownership tracking.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <div style="font-size: 1.5rem; margin-bottom: 0.75rem;">📋</div>
      <h4 style="font-size: 1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Data Quality Dashboard</h4>
      <p style="font-size: 0.875rem; color: #64748b;">Real-time governance score, linkage stats, and duplicate detection.</p>
    </div>
    
  </div>
</div>

<!-- Reports Section -->
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 1rem;">
  <h2 style="text-align: center; font-size: clamp(2rem, 4vw, 2.5rem); font-weight: 700; color: white; margin-bottom: 0.5rem;">
    📈 Reports
  </h2>
  <p style="text-align: center; font-size: 1.125rem; color: #64748b; margin-bottom: 3rem;">
    Comprehensive reporting for financial and operational insights
  </p>

  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <h4 style="font-size: 1rem; font-weight: 600; color: #06b6d4; margin-bottom: 0.5rem;">📊 Party Master Ledger</h4>
      <p style="font-size: 0.875rem; color: #94a3b8;">Consolidated ledger view across all linked parties with filters by Party Master, party type, company, and date range.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <h4 style="font-size: 1rem; font-weight: 600; color: #10b981; margin-bottom: 0.5rem;">💰 Party Account Balances</h4>
      <p style="font-size: 0.875rem; color: #94a3b8;">Account balance reporting per party with receivable/payable balances, currency-wise breakdown, and aging analysis.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <h4 style="font-size: 1rem; font-weight: 600; color: #f59e0b; margin-bottom: 0.5rem;">📋 Party Accounting Ledger</h4>
      <p style="font-size: 0.875rem; color: #94a3b8;">Detailed accounting transactions filtered by Party Master and accounting dimension with voucher-wise details.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <h4 style="font-size: 1rem; font-weight: 600; color: #ef4444; margin-bottom: 0.5rem;">🏥 Party Master Health Report</h4>
      <p style="font-size: 0.875rem; color: #94a3b8;">Data quality and governance reporting including linkage status, missing tax IDs, and data completeness metrics.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <h4 style="font-size: 1rem; font-weight: 600; color: #a855f7; margin-bottom: 0.5rem;">📅 Chronological Party Ledger</h4>
      <p style="font-size: 0.875rem; color: #94a3b8;">Time-based party transaction history with chronological listing and date-wise summaries.</p>
    </div>
    
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 1.25rem;">
      <h4 style="font-size: 1rem; font-weight: 600; color: #3b82f6; margin-bottom: 0.5rem;">📄 Party Account Statement</h4>
      <p style="font-size: 0.875rem; color: #94a3b8;">Customer/statement-style reporting in statement format ready for balance confirmation.</p>
    </div>
    
  </div>
</div>

<!-- Use Cases Section -->
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 1rem;">
  <h2 style="text-align: center; font-size: clamp(2rem, 4vw, 2.5rem); font-weight: 700; color: white; margin-bottom: 0.5rem;">
    🎯 Use Cases
  </h2>
  <p style="text-align: center; font-size: 1.125rem; color: #64748b; margin-bottom: 3rem;">
    Real-world scenarios where UPH adds value
  </p>

  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
    
    <div style="background: linear-gradient(135deg, rgba(37, 99, 235, 0.2) 0%, rgba(124, 58, 237, 0.2) 100%); border: 1px solid rgba(37, 99, 235, 0.3); border-radius: 16px; padding: 2rem;">
      <div style="font-size: 2.5rem; margin-bottom: 1rem;">🏢</div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">Conglomerates</h3>
      <p style="font-size: 0.95rem; color: #94a3b8; line-height: 1.7;">Manage inter-company transactions where a subsidiary is both a vendor and a client. Consolidate reporting across entities while maintaining individual entity visibility.</p>
    </div>
    
    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(6, 182, 212, 0.2) 100%); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 2rem;">
      <div style="font-size: 2.5rem; margin-bottom: 1rem;">🌍</div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">Multi-National Trade</h3>
      <p style="font-size: 0.95rem; color: #94a3b8; line-height: 1.7;">Handle single customers paying in multiple currencies without cluttering the Customer master. Automatic GL account resolution per currency.</p>
    </div>
    
    <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.2) 0%, rgba(239, 68, 68, 0.2) 100%); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 16px; padding: 2rem;">
      <div style="font-size: 2.5rem; margin-bottom: 1rem;">✅</div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">Governance Compliance</h3>
      <p style="font-size: 0.95rem; color: #94a3b8; line-height: 1.7;">Enforce strict Tax ID validation and prevent duplicate customer creation across different sales teams. Real-time governance scoring.</p>
    </div>
    
    <div style="background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(124, 58, 237, 0.2) 100%); border: 1px solid rgba(168, 85, 247, 0.3); border-radius: 16px; padding: 2rem;">
      <div style="font-size: 2.5rem; margin-bottom: 1rem;">🏭</div>
      <h3 style="font-size: 1.25rem; font-weight: 600; color: white; margin-bottom: 0.75rem;">Branch Accounting</h3>
      <p style="font-size: 0.95rem; color: #94a3b8; line-height: 1.7;">Track financial performance by branch/site without creating separate Customer/Supplier records. Oracle TCA-like site accounting.</p>
    </div>
    
  </div>
</div>

<!-- CTA Section -->
<div style="max-width: 1200px; margin: 4rem auto; padding: 0 1rem; text-align: center;">
  <div style="background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%); border-radius: 20px; padding: 4rem 2rem; position: relative; overflow: hidden;">
    <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"); opacity: 0.5;"></div>
    <div style="position: relative; z-index: 1;">
      <h2 style="font-size: clamp(2rem, 4vw, 2.5rem); font-weight: 700; color: white; margin-bottom: 1rem;">Ready to Transform Your Party Data?</h2>
      <p style="font-size: 1.125rem; color: rgba(255, 255, 255, 0.9); margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">Join thousands of organizations using UPH to centralize and govern their master data.</p>
      <a href="./docs/introduction/installation/" style="display: inline-flex; align-items: center; gap: 0.75rem; padding: 1.25rem 2.5rem; font-size: 1.125rem; font-weight: 700; border-radius: 12px; border: none; cursor: pointer; text-decoration: none; background: white; color: #2563eb; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);">
        <i class="fas fa-download"></i> Install Now
      </a>
    </div>
  </div>
</div>

<!-- GitHub Section -->
<div style="text-align:center; margin: 4rem 0; padding: 2rem;">
  <p style="font-size: 1rem; color: #64748b; margin-bottom: 1.5rem;">Support the project by starring us on GitHub</p>
  <iframe src="https://ghbtns.com/github-btn.html?user=Sendipad&repo=uph&type=star&count=true&size=large" frameborder="0" scrolling="0" width="170" height="30" title="GitHub"></iframe>
</div>

<style>
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.feature-card:hover {
  transform: translateY(-8px);
  border-color: rgba(37, 99, 235, 0.3);
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
}

.feature-card:hover::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  opacity: 1;
}
</style>
