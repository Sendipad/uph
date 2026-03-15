frappe.pages["uph-setup-wizard"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("UPH Setup Wizard"),
		single_column: true,
	});

	class SetupWizard {
		constructor(page) {
			this.page = page;
			this.step = 1;
			this.total_steps = 5;
			this.settings = {};
			this.templates = [];
			this.languages = [];
			this.has_data = false;

			this.load_status();
		}

		load_status() {
			frappe.call({
				method: "uph.party.page.uph_setup_wizard.uph_setup_wizard.get_setup_status",
				callback: (r) => {
					if (r.message) {
						if (r.message.setup_finished) {
							this.show_finished_screen();
						} else {
							this.has_data = r.message.has_data;
							this.languages = r.message.languages || [];
							this.load_templates();
						}
					}
				},
			});
		}

		load_templates() {
			frappe.call({
				method: "uph.party.page.uph_setup_wizard.uph_setup_wizard.get_tree_templates",
				callback: (r) => {
					this.templates = r.message || [];
					this.render();
				},
			});
		}

		render() {
			this.page.main.empty();
			let content = $(
				`<div class="uph-wizard-container" style="max-width: 800px; margin: 0 auto; padding: 20px;"></div>`
			).appendTo(this.page.main);

			if (this.step === 1) {
				this.render_intro(content);
			} else if (this.step === 2) {
				this.render_settings(content);
			} else if (this.step === 3) {
				this.render_templates(content);
			} else if (this.step === 4) {
				this.render_data_check(content);
			} else if (this.step === 5) {
				this.render_completion(content);
			}
		}

		render_intro(parent) {
			$(`
                <div class="text-center">
                    <img src="/assets/uph/images/uph_logo.png" style="max-height: 100px; margin-bottom: 20px;" onerror="this.style.display='none'">
                    <h1>${__("Welcome to Unified Party Hub")}</h1>
                    <p class="lead">${__("Let's set up your Master Data Management system.")}</p>
                    <hr>
                    <p>${__(
						"We will configure numbering, governance rules, and your initial party structure."
					)}</p>
                    <br>
                    <button class="btn btn-primary btn-lg" id="btn-start">${__(
						"Get Started"
					)}</button>
                </div>
            `).appendTo(parent);

			parent.find("#btn-start").on("click", () => {
				this.step++;
				this.render();
			});
		}

		render_settings(parent) {
			let lang_options = this.languages
				.map((l) => `<option value="${l.name}">${__(l.language_name)}</option>`)
				.join("");

			let html = `
                <h3>${__("Step 1: Configuration")}</h3>
                <div class="row">
                    <div class="col-sm-6">
                        <div class="form-group">
                            <label>${__("Setup Language")}</label>
                            <select class="form-control" id="uph-lang">
                                <option value="">${__("Select Language...")}</option>
                                ${lang_options}
                            </select>
                            <p class="help-block">${__(
								"Initial chart of parties will be Seeded in this language."
							)}</p>
                        </div>
                    </div>
                </div>
                <hr>
                <div class="form-group">
                    <label>${__("Numbering Format")}</label>
                    <select class="form-control" id="uph-format">
                        <option value="Concatenated">${__("Concatenated (e.g. 110010)")}</option>
                        <option value="Dash-Separated">${__(
							"Dash-Separated (e.g. 1100-10)"
						)}</option>
                    </select>
                </div>
                <div class="row">
                    <div class="col-sm-6">
                        <div class="form-group">
                            <label>${__("Leaf Digits Count")}</label>
                            <input type="number" class="form-control" id="uph-digits" value="6">
                        </div>
                    </div>
                    <div class="col-sm-6">
                        <div class="form-group">
                            <label>${__("Group Digits Count")}</label>
                            <input type="number" class="form-control" id="uph-group-digits" value="4">
                        </div>
                    </div>
                </div>
                <hr>
                <div class="checkbox">
                    <label><input type="checkbox" id="uph-unique"> ${__(
						"Enforce Cross-Type Uniqueness"
					)}</label>
                </div>
                <div class="checkbox">
                    <label><input type="checkbox" id="uph-sync" checked> ${__(
						"Sync ERPNext Party Roles"
					)}</label>
                </div>
                <br>
                <button class="btn btn-default" id="btn-back">${__("Back")}</button>
                <button class="btn btn-primary" id="btn-next">${__("Next")}</button>
            `;
			parent.html(html);

			// Restore values
			if (this.settings.language) $("#uph-lang").val(this.settings.language);
			if (this.settings.digits_count) $("#uph-digits").val(this.settings.digits_count);
			if (this.settings.group_digits) $("#uph-group-digits").val(this.settings.group_digits);

			parent.find("#btn-back").on("click", () => {
				this.step--;
				this.render();
			});
			parent.find("#btn-next").on("click", () => {
				this.settings.language = $("#uph-lang").val();
				this.settings.numbering_format = $("#uph-format").val();
				this.settings.digits_count = parseInt($("#uph-digits").val());
				this.settings.group_digits = parseInt($("#uph-group-digits").val());
				this.settings.enforce_cross_type_uniqueness = $("#uph-unique").is(":checked")
					? 1
					: 0;
				this.settings.sync_erp_party_naming = $("#uph-sync").is(":checked") ? 1 : 0;
				this.step++;
				this.render();
			});
		}

		render_templates(parent) {
			let html = `<h3>${__("Step 2: Choose Structure")}</h3><div class="list-group">`;

			this.templates.forEach((t) => {
				html += `
                    <a href="#" class="list-group-item template-item" data-id="${t.id}">
                        <h4 class="list-group-item-heading">${__(t.name)}</h4>
                        <p class="list-group-item-text">
                            ${__("Includes")}: ${t.preview
					.map((p) => __(p.party_name))
					.join(", ")} ...
                        </p>
                    </a>
                 `;
			});
			html += `</div>
                <br>
                 <button class="btn btn-default" id="btn-back">${__("Back")}</button>
             `;

			parent.html(html);

			parent.find("#btn-back").on("click", () => {
				this.step--;
				this.render();
			});
			parent.find(".template-item").on("click", (e) => {
				let id = $(e.currentTarget).data("id");
				this.settings.template_id = id;
				this.step++;
				this.render();
				return false;
			});
		}

		render_data_check(parent) {
			if (!this.has_data) {
				this.step++;
				this.render();
				return;
			}

			let html = `
                <h3>${__("Data Detected")}</h3>
                <div class="alert alert-info">
                    ${__(
						"Existing records found in Party Master. How do you want to proceed with the selected template structure?"
					)}
                </div>

                <div class="radio">
                    <label><input type="radio" name="uph-proceed" value="skip" checked> ${__(
						"Skip Seeding (Keep existing data as is)"
					)}</label>
                </div>
                <div class="radio">
                    <label><input type="radio" name="uph-proceed" value="update"> ${__(
						"Merge/Update (Overwrite conflicting records if any)"
					)}</label>
                </div>
                <div class="radio">
                    <label><input type="radio" name="uph-proceed" value="fresh"> ${__(
						"Fresh Start (Keep existing, but strictly seed new records)"
					)}</label>
                </div>

                <div class="checkbox" id="uph-conflict-container" style="display:none; margin-left: 20px;">
                    <label><input type="checkbox" id="uph-update-existing" checked> ${__(
						"Update existing records when conflict occurs"
					)}</label>
                </div>

                <br>
                <button class="btn btn-default" id="btn-back">${__("Back")}</button>
                <button class="btn btn-primary" id="btn-next">${__("Next")}</button>
            `;
			parent.html(html);

			parent.find('input[name="uph-proceed"]').on("change", function () {
				if ($(this).val() === "update") {
					$("#uph-conflict-container").show();
				} else {
					$("#uph-conflict-container").hide();
				}
			});

			parent.find("#btn-back").on("click", () => {
				this.step--;
				this.render();
			});
			parent.find("#btn-next").on("click", () => {
				let choice = parent.find('input[name="uph-proceed"]:checked').val();
				this.settings.skip_seeding = choice === "skip";
				this.settings.update_existing =
					choice === "update" && $("#uph-update-existing").is(":checked");
				this.step++;
				this.render();
			});
		}

		render_completion(parent) {
			let html = `
                <h3>${__("Ready to Setup?")}</h3>
                <p>${__("We will apply the following settings:")}</p>
                <ul>
                    <li>${__("Format")}: ${__(this.settings.numbering_format)}</li>
                    <li>${__("Digits")}: ${this.settings.digits_count}</li>
                    <li>${__("Structure")}: ${__(this.settings.template_id)}</li>
                </ul>
                <div class="alert alert-warning">
                    ${__("This action will lock core settings and generate the initial tree.")}
                </div>
                <button class="btn btn-default" id="btn-back">${__("Back")}</button>
                <button class="btn btn-success" id="btn-finish">${__("Finish Setup")}</button>
            `;
			parent.html(html);

			parent.find("#btn-back").on("click", () => {
				this.step--;
				this.render();
			});
			parent.find("#btn-finish").on("click", () => {
				this.apply_setup();
			});
		}

		apply_setup() {
			frappe.call({
				method: "uph.party.page.uph_setup_wizard.uph_setup_wizard.apply_setup_settings",
				args: {
					settings: JSON.stringify(this.settings),
					template_id: this.settings.template_id,
				},
				freeze: true,
				callback: (r) => {
					if (r.message && r.message.success) {
						this.show_finished_screen();
					}
				},
			});
		}

		show_finished_screen() {
			this.page.main.empty();
			$(`
                <div class="text-center" style="padding: 50px;">
                    <div class="text-success" style="font-size: 48px; margin-bottom: 20px;">
                        <span class="fa fa-check-circle"></span>
                    </div>
                    <h1>${__("Setup Complete!")}</h1>
                    <p class="lead">${__("UPH is now ready to use.")}</p>
                    <br>
                    <a href="/app/party-master" class="btn btn-primary">${__(
						"Go to Party Master"
					)}</a>
                    <a href="/app/data-quality-dashboard" class="btn btn-default">${__(
						"Go to Dashboard"
					)}</a>
                </div>
            `).appendTo(this.page.main);
		}
	}

	new SetupWizard(page);
};
