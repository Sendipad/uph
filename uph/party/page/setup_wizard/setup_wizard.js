frappe.pages['setup-wizard'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'UPH Setup Wizard',
        single_column: true
    });

    class SetupWizard {
        constructor(page) {
            this.page = page;
            this.step = 1;
            this.total_steps = 4;
            this.settings = {};
            this.templates = [];

            this.load_status();
        }

        load_status() {
            frappe.call({
                method: "uph.party.page.setup_wizard.setup_wizard.get_setup_status",
                callback: (r) => {
                    if (r.message && r.message.setup_finished) {
                        this.show_finished_screen();
                    } else {
                        this.load_templates();
                    }
                }
            });
        }

        load_templates() {
            frappe.call({
                method: "uph.party.page.setup_wizard.setup_wizard.get_tree_templates",
                callback: (r) => {
                    this.templates = r.message || [];
                    this.render();
                }
            });
        }

        render() {
            this.page.main.empty();
            let content = $(`<div class="uph-wizard-container" style="max-width: 800px; margin: 0 auto; padding: 20px;"></div>`).appendTo(this.page.main);

            if (this.step === 1) {
                this.render_intro(content);
            } else if (this.step === 2) {
                this.render_settings(content);
            } else if (this.step === 3) {
                this.render_templates(content);
            } else if (this.step === 4) {
                this.render_completion(content);
            }
        }

        render_intro(parent) {
            $(`
                <div class="text-center">
                    <img src="/assets/uph/images/uph_logo.png" style="max-height: 100px; margin-bottom: 20px;" onerror="this.style.display='none'">
                    <h1>Welcome to Unified Party Hub</h1>
                    <p class="lead">Let's set up your Master Data Management system.</p>
                    <hr>
                    <p>We will configure numbering, governance rules, and your initial party structure.</p>
                    <br>
                    <button class="btn btn-primary btn-lg" id="btn-start">Get Started</button>
                </div>
            `).appendTo(parent);

            parent.find('#btn-start').on('click', () => { this.step++; this.render(); });
        }

        render_settings(parent) {
            let html = `
                <h3>Step 1: Numbering & Governance</h3>
                <div class="form-group">
                    <label>Numbering Format</label>
                    <select class="form-control" id="uph-format">
                        <option value="Concatenated">Concatenated (e.g. 110010)</option>
                        <option value="Dash-Separated">Dash-Separated (e.g. 1100-10)</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Digits Count (per block)</label>
                    <input type="number" class="form-control" id="uph-digits" value="4">
                </div>
                <hr>
                <div class="checkbox">
                    <label><input type="checkbox" id="uph-unique"> Enforce Cross-Type Uniqueness</label>
                    <p class="help-block">Prevent creating a Supplier with the same name as a Customer.</p>
                </div>
                <div class="checkbox">
                    <label><input type="checkbox" id="uph-sync" checked> Sync ERPNext Party Roles</label>
                    <p class="help-block">Automatically name ERPNext Customer/Supplier records based on Party Master number.</p>
                </div>
                <br>
                <button class="btn btn-default" id="btn-back">Back</button>
                <button class="btn btn-primary" id="btn-next">Next</button>
            `;
            parent.html(html);

            // Restore values if needed
            if (this.settings.digits_count) $('#uph-digits').val(this.settings.digits_count);

            parent.find('#btn-back').on('click', () => { this.step--; this.render(); });
            parent.find('#btn-next').on('click', () => {
                this.settings.numbering_format = $('#uph-format').val();
                this.settings.digits_count = parseInt($('#uph-digits').val());
                this.settings.enforce_cross_type_uniqueness = $('#uph-unique').is(':checked') ? 1 : 0;
                this.settings.sync_erp_party_naming = $('#uph-sync').is(':checked') ? 1 : 0;
                this.step++;
                this.render();
            });
        }

        render_templates(parent) {
            let html = `<h3>Step 2: Choose Structure</h3><div class="list-group">`;

            this.templates.forEach(t => {
                html += `
                    <a href="#" class="list-group-item template-item" data-id="${t.id}">
                        <h4 class="list-group-item-heading">${t.name}</h4>
                        <p class="list-group-item-text">
                            Includes: ${t.preview.map(p => p.party_name).join(', ')} ...
                        </p>
                    </a>
                 `;
            });
            html += `</div>
                <br>
                 <button class="btn btn-default" id="btn-back">Back</button>
             `;

            parent.html(html);

            parent.find('#btn-back').on('click', () => { this.step--; this.render(); });
            parent.find('.template-item').on('click', (e) => {
                let id = $(e.currentTarget).data('id');
                this.settings.template_id = id;
                this.step++;
                this.render();
                return false;
            });
        }

        render_completion(parent) {
            let html = `
                <h3>Ready to Setup?</h3>
                <p>We will apply the following settings:</p>
                <ul>
                    <li>Format: ${this.settings.numbering_format}</li>
                    <li>Digits: ${this.settings.digits_count}</li>
                    <li>Structure: ${this.settings.template_id}</li>
                </ul>
                <div class="alert alert-warning">
                    This action will lock core settings and generate the initial tree.
                </div>
                <button class="btn btn-default" id="btn-back">Back</button>
                <button class="btn btn-success" id="btn-finish">Finish Setup</button>
            `;
            parent.html(html);

            parent.find('#btn-back').on('click', () => { this.step--; this.render(); });
            parent.find('#btn-finish').on('click', () => { this.apply_setup(); });
        }

        apply_setup() {
            frappe.call({
                method: "uph.party.page.setup_wizard.setup_wizard.apply_setup_settings",
                args: {
                    settings: JSON.stringify(this.settings),
                    template_id: this.settings.template_id
                },
                freeze: true,
                callback: (r) => {
                    if (r.message && r.message.success) {
                        this.show_finished_screen();
                    }
                }
            });
        }

        show_finished_screen() {
            this.page.main.empty();
            $(`
                <div class="text-center" style="padding: 50px;">
                    <div class="text-success" style="font-size: 48px; margin-bottom: 20px;">
                        <span class="fa fa-check-circle"></span>
                    </div>
                    <h1>Setup Complete!</h1>
                    <p class="lead">UPH is now ready to use.</p>
                    <br>
                    <a href="/app/party-master" class="btn btn-primary">Go to Party Master</a>
                    <a href="/app/data-quality-dashboard" class="btn btn-default">Go to Dashboard</a>
                </div>
            `).appendTo(this.page.main);
        }
    }

    new SetupWizard(page);
}
