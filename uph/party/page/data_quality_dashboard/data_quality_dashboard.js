frappe.pages['data-quality-dashboard'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Data Quality Dashboard'),
        single_column: true
    });

    page.main.addClass('data-quality-dashboard');
    new DataQualityDashboard(page);
};

class DataQualityDashboard {
    constructor(page) {
        this.page = page;
        this.wrapper = $(page.main);
        this.current_offset = 0;
        this.limit = 50;
        this.min_score = 70;
        this.active_tab = 'duplicates';
        this.party_master_filter = null;

        // Unlinked tab state
        this.unlinked_offset = 0;
        this.unlinked_limit = 50;

        // Health tab state
        this.health_offset = 0;
        this.health_limit = 50;

        // Unlinked Vouchers tab state
        this.unlinked_vouchers_offset = 0;
        this.unlinked_vouchers_limit = 50;

        this.init();
    }

    init() {
        this.setup_page_actions();
        this.render_layout();
        this.setup_filters();
        this.load_stats();
        this.load_tab_content();
    }

    setup_filters() {
        const filter_row = this.wrapper.find('.dashboard-filters');

        // Clear containers
        const pm_container = filter_row.find('.pm-filter-container').empty();
        const dt_container = filter_row.find('.dt-filter-container').empty();

        this.party_master_field = frappe.ui.form.make_control({
            df: {
                label: '',
                fieldtype: 'Link',
                fieldname: 'party_master',
                options: 'Party Master',
                placeholder: __('Filter by Party Master'),
                get_query: () => ({ filters: { is_group: 0, disabled: 0 } }),
                change: () => {
                    this.party_master_filter = this.party_master_field.get_value() || null;
                    this.current_offset = 0;
                    this.unlinked_offset = 0;
                    this.unlinked_vouchers_offset = 0;
                    this.health_offset = 0;
                    this.load_stats();
                    this.load_tab_content();
                }
            },
            parent: pm_container,
            render_input: true
        });

        this.doctype_filter_field = frappe.ui.form.make_control({
            df: {
                label: '',
                fieldtype: 'Link',
                fieldname: 'reference_doctype',
                options: 'DocType',
                placeholder: __('Filter by DocType'),
                get_query: () => {
                    const tx_doctypes = (frappe.boot.party_master_on_doctypes_depend_field || [])
                        .map(d => d[0]) // parent_doctype is at index 0
                        .filter((v, i, a) => a.indexOf(v) === i); // unique

                    if (tx_doctypes.length) {
                        return { filters: { name: ['in', tx_doctypes] } };
                    }
                    return { filters: { istable: 0, issingle: 0 } };
                },
                change: () => {
                    this.doctype_filter = this.doctype_filter_field.get_value() || null;
                    this.unlinked_vouchers_offset = 0;
                    this.health_offset = 0;
                    this.load_tab_content();
                }
            },
            parent: dt_container,
            render_input: true
        });

        // Hide initially since default tab is Duplicates
        dt_container.parent().hide();
    }

    setup_page_actions() {
        this.page.set_primary_action(__('Refresh'), () => {
            frappe.call({
                method: 'uph.party.page.data_quality_dashboard.data_quality_dashboard.run_all_scans',
                callback: (r) => {
                    const message = (r && r.message && r.message.message) || (r && r.message);
                    if (message) {
                        frappe.show_alert({ message, indicator: 'blue' });
                    }
                    this.load_stats();
                    this.load_tab_content();
                }
            });
        }, 'refresh');

        this.page.add_menu_item(__('Settings'), () => {
            this.show_settings_dialog();
        });

        this.page.add_menu_item(__('Run Duplicate Scan'), () => {
            frappe.call({
                method: 'uph.party.controllers.duplicate_scanner.enqueue_duplicate_scan',
                args: { min_score: this.min_score },
                callback: (r) => {
                    if (r.message && r.message.success) {
                        frappe.show_alert({ message: r.message.message, indicator: 'blue' });
                    }
                }
            });
        });
    }

    render_layout() {
        this.wrapper.html(`
            <div class="data-quality-container" style="padding: 1rem;">
                <!-- Stats Cards - Frappe Number Card Style -->
                <div class="stats-row" style="display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap;">
                    <div class="stat-card" id="stat-total-parties" data-route="" style="flex: 1; min-width: 140px; padding: 1rem 1rem 1rem 1.25rem; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow-sm); border-left: 4px solid var(--blue-500); cursor: default;">
                        <div class="stat-label" style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.25rem;">${__('Total Parties')}</div>
                        <div class="stat-value" style="font-size: 1.75rem; font-weight: 700;">-</div>
                    </div>
                    <div class="stat-card stat-clickable" id="stat-duplicate-issues" data-issue-type="Duplicate" style="flex: 1; min-width: 140px; padding: 1rem 1rem 1rem 1.25rem; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow-sm); border-left: 4px solid var(--orange-500); cursor: pointer;">
                        <div class="stat-label" style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.25rem;">${__('Duplicate Issues')}</div>
                        <div class="stat-value" style="font-size: 1.75rem; font-weight: 700; color: var(--orange-500);">-</div>
                    </div>
                    <div class="stat-card stat-clickable" id="stat-unlinked" data-issue-type="Unlinked" style="flex: 1; min-width: 140px; padding: 1rem 1rem 1rem 1.25rem; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow-sm); border-left: 4px solid var(--purple-500); cursor: pointer;">
                        <div class="stat-label" style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.25rem;">${__('Unlinked Roles')}</div>
                        <div class="stat-value" style="font-size: 1.75rem; font-weight: 700; color: var(--purple-500);">-</div>
                    </div>
                    <div class="stat-card stat-clickable" id="stat-policy-issues" data-issue-type="Transaction Policy" style="flex: 1; min-width: 140px; padding: 1rem 1rem 1rem 1.25rem; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow-sm); border-left: 4px solid var(--red-500); cursor: pointer;">
                        <div class="stat-label" style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.25rem;">${__('Transaction Health')}</div>
                        <div class="stat-value" style="font-size: 1.75rem; font-weight: 700; color: var(--red-500);">-</div>
                    </div>
                </div>

                <!-- Filters Row (Moved below stats) -->
                <div class="dashboard-filters" style="display: flex; gap: 1rem; margin-bottom: 1.5rem; align-items: center; background: var(--card-bg); padding: 0.75rem 1rem; border-radius: 8px; box-shadow: var(--shadow-sm); border: 1px solid var(--border-color);">
                    <div style="flex: 1; min-width: 200px;">
                        <div class="pm-filter-container"></div>
                    </div>
                    <div style="flex: 1; min-width: 200px;">
                        <div class="dt-filter-container"></div>
                    </div>
                    <div style="flex: 2;"></div>
                </div>

                <!-- Tab Links -->
                <ul class="nav nav-tabs" role="tablist" style="margin-bottom: 1rem;">
                    <li class="nav-item">
                        <a class="nav-link active" data-tab="duplicates" href="#" role="tab">
                            ${__('Duplicates')}
                            <span class="badge badge-pill" id="tab-badge-dups" style="margin-left: 4px;"></span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="unlinked" href="#" role="tab">
                            ${__('Unlinked Roles')}
                            <span class="badge badge-pill" id="tab-badge-unlinked" style="margin-left: 4px;"></span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="unlinked_vouchers" href="#" role="tab">
                            ${__('Unlinked Vouchers')}
                            <span class="badge badge-pill" id="tab-badge-unlinked-vouchers" style="margin-left: 4px;"></span>
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-tab="health" href="#" role="tab">
                            ${__('Transaction Health')}
                            <span class="badge badge-pill" id="tab-badge-health" style="margin-left: 4px;"></span>
                        </a>
                    </li>
                </ul>

                <!-- Tab Content -->
                <div class="tab-content-area" id="tab-content">
                    <div class="text-muted">${__('Loading...')}</div>
                </div>
                <div class="pagination-controls" id="pagination" style="margin-top: 1rem; display: flex; gap: 0.5rem; justify-content: center;"></div>
            </div>
        `);

        // Bind tab clicks
        this.wrapper.find('.nav-link').on('click', (e) => {
            e.preventDefault();
            const tab = $(e.currentTarget).data('tab');
            this.switch_tab(tab);
        });

        // Bind stat card clicks → navigate to Party Issue list
        this.wrapper.find('.stat-clickable').on('click', (e) => {
            const $card = $(e.currentTarget).closest('.stat-card');
            const issue_type = $card.data('issue-type');
            const status = $card.data('status');
            let filters = {};
            if (issue_type) {
                filters['issue_type'] = issue_type;
                filters['status'] = ['in', ['Open', 'Under Review']];
            }
            if (status) {
                filters['status'] = status;
            }
            frappe.set_route('List', 'Party Issue', filters);
        });
    }

    switch_tab(tab) {
        this.active_tab = tab;
        this.wrapper.find('.nav-link').removeClass('active');
        this.wrapper.find(`.nav-link[data-tab="${tab}"]`).addClass('active');

        // Show/hide DocType filter based on tab
        const dt_container = this.wrapper.find('.dt-filter-container').parent();
        if (tab === 'unlinked_vouchers' || tab === 'health') {
            dt_container.show();
        } else {
            dt_container.hide();
        }

        this.load_tab_content();
    }

    load_tab_content() {
        if (this.active_tab === 'duplicates') {
            this.load_duplicates();
        } else if (this.active_tab === 'unlinked') {
            this.load_unlinked();
        } else if (this.active_tab === 'unlinked_vouchers') {
            this.load_unlinked_vouchers();
        } else if (this.active_tab === 'health') {
            this.load_health();
        }
    }

    load_stats() {
        frappe.call({
            method: 'uph.party.page.data_quality_dashboard.data_quality_dashboard.get_dashboard_stats',
            args: { party_master: this.party_master_filter || '' },
            callback: (r) => {
                if (r.message) {
                    this.update_stats(r.message);
                }
            }
        });
    }

    update_stats(stats) {
        $('#stat-total-parties .stat-value').text(stats.total_parties || 0);
        $('#stat-duplicate-issues .stat-value').text(stats.duplicate_issues || 0);
        $('#stat-unlinked .stat-value').text(stats.unlinked_count || 0);

        // Transaction Health stat card update (using ID from render_layout)
        const health_total = (stats.draft_voucher_count || 0) + (stats.cancelled_unamended_count || 0);
        $('#stat-policy-issues .stat-value').text(health_total);

        // Update tab badges
        if (stats.duplicate_issues) {
            $('#tab-badge-dups').text(stats.duplicate_issues).show();
        } else {
            $('#tab-badge-dups').hide();
        }
        if (stats.unlinked_count) {
            $('#tab-badge-unlinked').text(stats.unlinked_count).show();
        } else {
            $('#tab-badge-unlinked').hide();
        }

        if (health_total) {
            $('#tab-badge-health').text(health_total).show();
        } else {
            $('#tab-badge-health').hide();
        }
    }

    // ═══════════════════════════════════════════
    // DUPLICATES TAB
    // ═══════════════════════════════════════════

    load_duplicates() {
        const content = $('#tab-content');
        content.html(`<div class="text-muted">${__('Loading duplicates...')}</div>`);

        frappe.call({
            method: 'uph.party.page.data_quality_dashboard.data_quality_dashboard.get_duplicate_issues',
            args: {
                limit: this.limit,
                offset: this.current_offset,
                min_score: this.min_score,
                party_master: this.party_master_filter || '',
            },
            callback: (r) => {
                if (r.message) {
                    this.render_duplicates(r.message);
                }
            }
        });
    }

    render_duplicates(data) {
        const content = $('#tab-content');
        content.empty();

        if (!data.duplicates || data.duplicates.length === 0) {
            content.html(`<div class="text-muted text-center" style="padding: 2rem;">${__('No potential duplicates found')}</div>`);
            this.render_pagination(0, 'duplicates');
            return;
        }

        data.duplicates.forEach((dup) => {
            const card = $(`
                <div class="duplicate-card" style="background: var(--card-bg); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: var(--shadow-sm);">
                    <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 1rem;">
                        <div style="flex: 1; min-width: 200px;">
                            <div style="font-weight: 600;">
                                <a href="/app/party-master/${dup.party_1}" target="_blank">${dup.party_1_name || dup.party_1}</a>
                            </div>
                            <div class="text-muted small">${dup.party_1 || '-'}</div>
                        </div>
                        <div style="text-align: center; padding: 0 1rem;">
                            <div class="similarity-badge" style="background: ${this.get_score_color(dup.similarity_score)}; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-weight: 600;">
                                ${dup.similarity_score}%
                            </div>
                            <div class="text-muted small" style="margin-top: 0.25rem;">${__('Similarity')}</div>
                        </div>
                        <div style="flex: 1; min-width: 200px; text-align: right;">
                            <div style="font-weight: 600;">
                                <a href="/app/party-master/${dup.party_2}" target="_blank">${dup.party_2_name || dup.party_2}</a>
                            </div>
                            <div class="text-muted small">${dup.party_2 || '-'}</div>
                        </div>
                    </div>
                    <div style="margin-top: 1rem; display: flex; gap: 0.5rem; justify-content: flex-end; align-items: center;">
                        <a href="/app/party-issue/${dup.name}" target="_blank" class="btn btn-default btn-sm" title="${__('Open Issue')}">
                            <i class="fa fa-external-link"></i>
                        </a>
                        <div style="flex: 1;"></div>
                        <button class="btn btn-default btn-sm btn-dismiss" data-party1="${dup.party_1}" data-party2="${dup.party_2}">
                            ${__('Not a Duplicate')}
                        </button>
                        <button class="btn btn-primary btn-sm btn-merge" data-party1="${dup.party_1}" data-party2="${dup.party_2}">
                            ${__('Merge')}
                        </button>
                    </div>
                </div>
            `);

            card.find('.btn-dismiss').on('click', (e) => {
                const $btn = $(e.currentTarget);
                this.dismiss_duplicate($btn.data('party1'), $btn.data('party2'));
            });

            card.find('.btn-merge').on('click', (e) => {
                const $btn = $(e.currentTarget);
                this.show_merge_dialog($btn.data('party1'), $btn.data('party2'));
            });

            content.append(card);
        });

        this.render_pagination(data.total, 'duplicates');
    }

    get_score_color(score) {
        if (score >= 90) return 'var(--red-500)';
        if (score >= 80) return 'var(--orange-500)';
        return 'var(--yellow-600)';
    }

    dismiss_duplicate(party1, party2) {
        frappe.prompt({
            label: __('Reason'),
            fieldname: 'reason',
            fieldtype: 'Small Text',
            reqd: 1
        }, (values) => {
            frappe.call({
                method: 'uph.party.page.data_quality_dashboard.data_quality_dashboard.dismiss_duplicate',
                args: {
                    party_1: party1,
                    party_2: party2,
                    reason: values.reason
                },
                callback: (r) => {
                    if (r.message && r.message.success) {
                        frappe.show_alert({ message: r.message.message, indicator: 'green' });
                        this.load_stats();
                        this.load_duplicates();
                    }
                }
            });
        }, __('Dismiss Duplicate'), __('Dismiss'));
    }

    show_merge_dialog(party1, party2) {
        if (!party1 || !party2) {
            frappe.msgprint(__('Unable to resolve the selected parties. Please refresh and try again.'));
            return;
        }
        if (party1 === party2) {
            frappe.msgprint(__('Cannot merge a party with itself.'));
            return;
        }
        const d = new frappe.ui.Dialog({
            title: __('Merge Parties'),
            fields: [
                {
                    fieldname: 'primary_party',
                    fieldtype: 'Select',
                    label: __('Keep (Primary Party)'),
                    options: [party1, party2].join('\n'),
                    default: party1,
                    reqd: 1,
                    onchange: () => {
                        const primary = d.get_value('primary_party');
                        const secondary = primary === party1 ? party2 : party1;
                        d.set_value('secondary_party', secondary);
                    }
                },
                {
                    fieldname: 'secondary_party',
                    fieldtype: 'Data',
                    label: __('Merge (Secondary Party)'),
                    read_only: 1,
                    default: party2
                },
                {
                    fieldname: 'info',
                    fieldtype: 'HTML',
                    options: `<div class="alert alert-warning">
                        ${__('The secondary party will be merged into the primary party and deleted. All linked documents will be updated.')}
                    </div>`
                }
            ],
            primary_action_label: __('Merge'),
            primary_action: (values) => {
                const primary = values.primary_party;
                const secondary = values.secondary_party || (primary === party1 ? party2 : party1);

                frappe.confirm(
                    __('Are you sure you want to merge {0} into {1}? This action cannot be undone.', [secondary, primary]),
                    () => {
                        d.hide();
                        this.execute_merge(primary, secondary);
                    }
                );
            }
        });
        d.show();
    }

    execute_merge(primary, secondary) {
        frappe.call({
            method: 'uph.party.page.data_quality_dashboard.data_quality_dashboard.merge_parties',
            args: {
                primary_party: primary,
                secondary_party: secondary
            },
            freeze: true,
            freeze_message: __('Merging parties...'),
            callback: (r) => {
                if (r.message && r.message.success) {
                    frappe.show_alert({ message: r.message.message, indicator: 'green' });
                    this.load_stats();
                    this.load_duplicates();
                }
            }
        });
    }

    // ═══════════════════════════════════════════
    // UNLINKED ROLES TAB
    // ═══════════════════════════════════════════

    load_unlinked() {
        const content = $('#tab-content');
        content.html(`<div class="text-muted">${__('Loading unlinked roles...')}</div>`);

        frappe.call({
            method: 'uph.party.controllers.unlinked_resolver.get_unlinked_issues',
            args: {
                limit: this.unlinked_limit,
                offset: this.unlinked_offset,
                party_master: this.party_master_filter || '',
            },
            callback: (r) => {
                if (r.message) {
                    this.render_unlinked(r.message);
                }
            }
        });
    }

    render_unlinked(data) {
        const content = $('#tab-content');
        content.empty();

        if (!data.unlinked || data.unlinked.length === 0) {
            content.html(`<div class="text-muted text-center" style="padding: 2rem;">${__('All role records are linked to a Party Master')}</div>`);
            this.render_pagination(0, 'unlinked');
            return;
        }

        // Header
        content.append(`
            <div style="display: flex; padding: 0.5rem 1rem; font-weight: 600; color: var(--text-muted); font-size: 0.85rem; border-bottom: 1px solid var(--border-color);">
                <div style="flex: 2;">${__('Record')}</div>
                <div style="flex: 1;">${__('Type')}</div>
                <div style="flex: 1;">${__('Currency')}</div>
                <div style="flex: 1; text-align: right;">${__('Actions')}</div>
            </div>
        `);

        data.unlinked.forEach((item) => {
            const row = $(`
                <div class="unlinked-row" style="display: flex; align-items: center; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color); background: var(--card-bg);">
                    <div style="flex: 2;">
                        <div style="font-weight: 500;">
                            <a href="/app/${frappe.router.slug(item.role_doctype)}/${item.role_name}" target="_blank">${item.display_name}</a>
                        </div>
                        <div class="text-muted small">${item.role_name}</div>
                    </div>
                    <div style="flex: 1;">
                        <span class="indicator-pill" style="font-size: 0.8rem;">${item.role_doctype}</span>
                    </div>
                    <div style="flex: 1;">${item.currency || '-'}</div>
                    <div style="flex: 1; text-align: right; display: flex; gap: 0.5rem; justify-content: flex-end;">
                        <a href="/app/party-issue/${item.issue}" target="_blank" class="btn btn-default btn-xs" title="${__('Open Issue')}">
                            <i class="fa fa-external-link"></i>
                        </a>
                        <button class="btn btn-default btn-xs btn-suggest" data-doctype="${item.role_doctype}" data-name="${item.role_name}" data-display="${item.display_name}">
                            ${__('Find & Link')}
                        </button>
                    </div>
                </div>
            `);

            row.find('.btn-suggest').on('click', (e) => {
                const $btn = $(e.currentTarget);
                this.show_link_dialog($btn.data('doctype'), $btn.data('name'), $btn.data('display'));
            });

            content.append(row);
        });

        this.render_pagination(data.total, 'unlinked');
    }

    show_link_dialog(role_doctype, role_name, display_name) {
        const d = new frappe.ui.Dialog({
            title: __('Link {0} to Party Master', [display_name]),
            fields: [
                {
                    fieldname: 'suggestions_html',
                    fieldtype: 'HTML',
                    options: `<div class="text-muted">${__('Loading suggestions...')}</div>`,
                },
                { fieldtype: 'Section Break' },
                {
                    fieldname: 'party_master',
                    fieldtype: 'Link',
                    label: __('Party Master'),
                    options: 'Party Master',
                    get_query: () => ({ filters: { is_group: 0, disabled: 0 } }),
                    description: __('Select manually or pick from suggestions above'),
                }
            ],
            primary_action_label: __('Link'),
            primary_action: (values) => {
                if (!values.party_master) {
                    frappe.msgprint(__('Please select a Party Master'));
                    return;
                }
                frappe.call({
                    method: 'uph.party.controllers.unlinked_resolver.link_to_party_master',
                    args: {
                        role_doctype: role_doctype,
                        role_name: role_name,
                        party_master: values.party_master,
                    },
                    callback: (r) => {
                        if (r.message && r.message.success) {
                            d.hide();
                            frappe.show_alert({ message: r.message.message, indicator: 'green' });
                            this.load_stats();
                            this.load_unlinked();
                        }
                    }
                });
            }
        });
        d.show();

        // Load suggestions
        frappe.call({
            method: 'uph.party.controllers.unlinked_resolver.get_unlinked_suggestions',
            args: {
                role_doctype: role_doctype,
                role_name: role_name,
                limit: 5,
            },
            callback: (r) => {
                const suggestions = r.message && r.message.suggestions ? r.message.suggestions : [];
                const max_score = suggestions.length ? Math.max(...suggestions.map(s => s.score)) : 0;

                if (suggestions.length) {
                    let html = `<div style="margin-bottom: 0.5rem; font-weight: 600;">${__('Suggested Matches')}</div>`;
                    suggestions.forEach(s => {
                        html += `
                            <div class="suggestion-row" style="display: flex; align-items: center; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 6px; margin-bottom: 0.5rem; cursor: pointer;" data-pm="${s.party_master}">
                                <div style="flex: 2;">
                                    <div style="font-weight: 500;">${s.party_name}</div>
                                    <div class="text-muted small">${s.party_master} | ${__(s.party_type) || ''}</div>
                                </div>
                                <div style="flex: 1; text-align: right;">
                                    <span style="background: ${s.score >= 80 ? 'var(--green-100)' : 'var(--yellow-100)'}; color: ${s.score >= 80 ? 'var(--green-700)' : 'var(--yellow-700)'}; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.8rem; font-weight: 600;">
                                        ${s.score}%
                                    </span>
                                </div>
                            </div>
                        `;
                    });
                    d.fields_dict.suggestions_html.$wrapper.html(html);

                    // Click to select
                    d.fields_dict.suggestions_html.$wrapper.find('.suggestion-row').on('click', function () {
                        d.set_value('party_master', $(this).data('pm'));
                    });
                } else {
                    d.fields_dict.suggestions_html.$wrapper.html(
                        `<div class="text-muted">${__('No close matches found. Use the selector below.')}</div>`
                    );
                }

                // Show "Create New Party Master" button if suggestions are missing or low score
                if (max_score < 80) {
                    const create_btn = $(`
                        <div style="margin-top: 1rem; text-align: center;">
                            <button class="btn btn-primary btn-sm btn-create-pm">
                                <i class="fa fa-plus" style="margin-right: 5px;"></i>
                                ${__('Create New Party Master')}
                            </button>
                            <div class="text-muted small" style="margin-top: 5px;">
                                ${__('Create a new Party Master using quick entry')}
                            </div>
                        </div>
                    `);

                    create_btn.find('.btn-create-pm').on('click', () => {
                        d.hide();
                        this.open_party_master_quick_entry(role_doctype, role_name, display_name);
                    });

                    d.fields_dict.suggestions_html.$wrapper.append(create_btn);
                }
            }
        });
    }

    open_party_master_quick_entry(role_doctype, role_name, display_name) {
        const party_type = role_doctype || '';
        const role_name_fallback = display_name && display_name.includes(':') ? role_name : display_name;

        if (!role_doctype) {
            const new_doc = frappe.model.get_new_doc('Party Master');
            new_doc.party_name = role_name_fallback || role_name || __('New Party');
            new_doc.is_group = 0;
            frappe.ui.form.make_quick_entry('Party Master', null, null, new_doc);
            return;
        }

        frappe.model.with_doctype(role_doctype, () => {
            const has_field = (fieldname) => !!frappe.meta.get_docfield(role_doctype, fieldname);
            const candidate_fields = [
                'customer_name',
                'supplier_name',
                'employee_name',
                'default_currency',
                'default_price_list',
                'payment_terms',
                'territory',
                'language',
                'email_id',
                'mobile_no',
                'tax_id',
                'customer_group',
                'supplier_group',
            ];
            const fields = candidate_fields.filter((fieldname) => has_field(fieldname));
            fields.push('name');

            frappe.db.get_value(role_doctype, role_name, fields)
                .then((r) => {
                    const role = (r && r.message) || {};
                    const new_doc = frappe.model.get_new_doc('Party Master');

                    const party_name =
                        role.customer_name ||
                        role.supplier_name ||
                        role.employee_name ||
                        role_name_fallback ||
                        role.name ||
                        role_name;

                    new_doc.party_name = party_name;
                    new_doc.party_type = party_type;
                    new_doc.is_group = 0;

                    if (role.default_currency) new_doc.default_currency = role.default_currency;
                    if (role.default_price_list) new_doc.default_price_list = role.default_price_list;
                    if (role.payment_terms) new_doc.payment_terms = role.payment_terms;
                    if (role.territory) new_doc.territory = role.territory;
                    if (role.language) new_doc.language = role.language;
                    if (role.email_id) new_doc.email_id = role.email_id;
                    if (role.mobile_no) new_doc.mobile_no = role.mobile_no;
                    if (role.tax_id) new_doc.tax_id = role.tax_id;

                    if (role_doctype === 'Customer' && role.customer_group) {
                        new_doc.group_type = 'Customer Group';
                        new_doc.party_type_group = role.customer_group;
                    }
                    if (role_doctype === 'Supplier' && role.supplier_group) {
                        new_doc.group_type = 'Supplier Group';
                        new_doc.party_type_group = role.supplier_group;
                    }

                    frappe.ui.form.make_quick_entry(
                        'Party Master',
                        (doc) => {
                            frappe.call({
                                method: 'uph.party.controllers.unlinked_resolver.link_to_party_master',
                                args: {
                                    role_doctype: role_doctype,
                                    role_name: role_name,
                                    party_master: doc.name,
                                },
                                callback: (res) => {
                                    if (res.message && res.message.success) {
                                        frappe.show_alert({ message: res.message.message, indicator: 'green' });
                                        this.load_stats();
                                        this.load_unlinked();
                                    }
                                }
                            });
                        },
                        null,
                        new_doc
                    );
                });
        });
    }

    // ═══════════════════════════════════════════
    // TRANSACTION HEALTH TAB
    // ═══════════════════════════════════════════

    // ═══════════════════════════════════════════
    // UNLINKED VOUCHERS TAB
    // ═══════════════════════════════════════════

    load_unlinked_vouchers() {
        const content = $('#tab-content');
        content.html(`<div class="text-muted">${__('Loading unlinked vouchers...')}</div>`);

        frappe.call({
            method: 'uph.party.page.data_quality_dashboard.data_quality_dashboard.get_unlinked_voucher_issues',
            args: {
                limit: this.unlinked_vouchers_limit,
                offset: this.unlinked_vouchers_offset,
                party_master: this.party_master_filter || '',
                reference_doctype: this.doctype_filter || '',
            },
            callback: (r) => {
                if (r.message) {
                    this.render_unlinked_vouchers(r.message);
                }
            }
        });
    }

    render_unlinked_vouchers(data) {
        const content = $('#tab-content');
        content.empty();

        if (!data.unlinked || data.unlinked.length === 0) {
            content.html(`<div class="text-muted text-center" style="padding: 2rem;">${__('No unlinked voucher issues found')}</div>`);
            this.render_pagination(0, 'unlinked_vouchers');
            return;
        }

        // Header
        content.append(`
            <div style="display: flex; padding: 0.5rem 1rem; font-weight: 600; color: var(--text-muted); font-size: 0.85rem; border-bottom: 1px solid var(--border-color);">
                <div style="flex: 2;">${__('Voucher')}</div>
                <div style="flex: 1;">${__('Type')}</div>
                <div style="flex: 1;">${__('Created On')}</div>
                <div style="flex: 1; text-align: right;">${__('Actions')}</div>
            </div>
        `);

        data.unlinked.forEach((item) => {
            const row = $(`
                <div class="unlinked-row" style="display: flex; align-items: center; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color); background: var(--card-bg);">
                    <div style="flex: 2;">
                        <div style="font-weight: 500;">
                            <a href="/app/${frappe.router.slug(item.role_doctype)}/${item.role_name}" target="_blank">${item.display_name}</a>
                        </div>
                        <div class="text-muted small">${item.owner ? __('By') + ' ' + item.owner : item.role_name}</div>
                    </div>
                    <div style="flex: 1;">
                        <span class="indicator-pill" style="font-size: 0.8rem;">${__(item.role_doctype)}</span>
                    </div>
                    <div style="flex: 1;">${item.creation ? frappe.datetime.global_date_format(item.creation) : '-'}</div>
                    <div style="flex: 1; text-align: right; display: flex; gap: 0.5rem; justify-content: flex-end;">
                        ${item.issue_name ? `
                            <a href="/app/party-issue/${item.issue_name}" target="_blank" class="btn btn-default btn-xs" title="${__('Open Issue')}">
                                <i class="fa fa-external-link"></i>
                            </a>
                        ` : ''}
                        <button class="btn btn-default btn-xs btn-suggest" data-doctype="${item.role_doctype}" data-name="${item.role_name}" data-display="${item.display_name}">
                            ${__('Link')}
                        </button>
                    </div>
                </div>
            `);

            row.find('.btn-suggest').on('click', (e) => {
                const $btn = $(e.currentTarget);
                this.show_voucher_link_dialog($btn.data('doctype'), $btn.data('name'), $btn.data('display'), $btn.data('role'));
            });

            content.append(row);
        });

        this.render_pagination(data.total, 'unlinked_vouchers');
    }

    show_voucher_link_dialog(voucher_doctype, voucher_name, voucher_display, role_name) {
        // Find the mapped role doctype (e.g. Sales Invoice -> Customer)
        frappe.db.get_value('Party Master Settings', null, 'document_types')
            .then(() => {
                // To keep it simple, we ask the server for the role doctype/name of this voucher
                frappe.call({
                    method: 'frappe.client.get',
                    args: { doctype: voucher_doctype, name: voucher_name },
                    callback: (r) => {
                        if (r.message) {
                            const doc = r.message;
                            let role_doctype = '';
                            let actual_role_name = '';

                            // Guess the role field based on common patterns
                            if (doc.customer) { role_doctype = 'Customer'; actual_role_name = doc.customer; }
                            else if (doc.supplier) { role_doctype = 'Supplier'; actual_role_name = doc.supplier; }
                            else if (doc.employee) { role_doctype = 'Employee'; actual_role_name = doc.employee; }
                            else if (doc.party_type && doc.party) { role_doctype = doc.party_type; actual_role_name = doc.party; }

                            if (!role_doctype || !actual_role_name) {
                                frappe.msgprint(__('Could not determine the underlying party role (Customer/Supplier) for {0}', [voucher_display]));
                                return;
                            }

                            this._render_voucher_link_dialog(voucher_doctype, voucher_name, voucher_display, role_doctype, actual_role_name);
                        }
                    }
                });
            });
    }

    _render_voucher_link_dialog(voucher_doctype, voucher_name, voucher_display, role_doctype, role_name) {
        const d = new frappe.ui.Dialog({
            title: __('Link {0} to Party Master', [voucher_display]),
            fields: [
                {
                    fieldname: 'info',
                    fieldtype: 'HTML',
                    options: `
                        <div class="alert alert-info">
                            ${__('This voucher relies on the <b>{0}</b> record: <b>{1}</b>. By linking this {0} to a Party Master, this voucher (and all others using it) will be resolved.', [role_doctype, role_name])}
                        </div>
                    `
                },
                {
                    fieldname: 'party_master',
                    fieldtype: 'Link',
                    label: __('Party Master'),
                    options: 'Party Master',
                    get_query: () => ({ filters: { is_group: 0, disabled: 0 } }),
                    reqd: 1
                }
            ],
            primary_action_label: __('Link to Party Master'),
            primary_action: (values) => {
                frappe.call({
                    method: 'uph.party.controllers.unlinked_resolver.resolve_unlinked_voucher',
                    args: {
                        role_doctype: role_doctype,
                        role_name: role_name,
                        party_master: values.party_master,
                    },
                    callback: (r) => {
                        if (r.message && r.message.success) {
                            d.hide();
                            frappe.show_alert({ message: r.message.message, indicator: 'green' });
                            this.load_stats();
                            this.load_unlinked_vouchers();
                        }
                    }
                });
            }
        });
        d.show();
    }

    load_health() {
        const content = $('#tab-content');
        content.html(`<div class="text-muted">${__('Loading transaction health...')}</div>`);

        frappe.call({
            method: 'uph.party.controllers.transaction_health.get_transaction_health',
            args: {
                limit: this.health_limit,
                offset: this.health_offset,
                party_master: this.party_master_filter || '',
                reference_doctype: this.doctype_filter || '',
            },
            callback: (r) => {
                if (r.message) {
                    this.render_health(r.message);
                }
            }
        });
    }

    render_health(data) {
        const content = $('#tab-content');
        content.empty();

        if (!data.parties || data.parties.length === 0) {
            content.html(`<div class="text-muted text-center" style="padding: 2rem;">${__('No transaction health issues found')}</div>`);
            this.render_pagination(0, 'health');
            return;
        }

        // Header
        content.append(`
            <div style="display: flex; padding: 0.5rem 1rem; font-weight: 600; color: var(--text-muted); font-size: 0.85rem; border-bottom: 1px solid var(--border-color);">
                <div style="flex: 2;">${__('Party Master')}</div>
                <div style="flex: 1;">${__('DocType')}</div>
                <div style="flex: 1; text-align: center;">${__('Drafts')}</div>
                <div style="flex: 1; text-align: center;">${__('Cancelled')}</div>
                <div style="flex: 1; text-align: center;">${__('Severity')}</div>
                <div style="flex: 1; text-align: right;">${__('Actions')}</div>
            </div>
        `);

        data.parties.forEach(p => {
            const severity_color = p.severity === 'Critical' ? 'var(--red-700)' : (p.severity === 'High' ? 'var(--red-500)' : (p.severity === 'Medium' ? 'var(--orange-500)' : 'var(--yellow-600)'));
            const row = $(`
                <div class="health-row" style="display: flex; align-items: center; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color); background: var(--card-bg);">
                    <div style="flex: 2;">
                        <div style="font-weight: 500;">
                            <a href="/app/party-master/${p.party_master}" target="_blank">${p.party_name}</a>
                        </div>
                        <div class="text-muted small">${p.party_number || '-'} | ${__(p.party_type) || ''}</div>
                    </div>
                    <div style="flex: 1;">
                        <span class="indicator-pill" style="font-size: 0.75rem;">${__(p.reference_doctype) || '-'}</span>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-weight: 600; color: ${p.draft_count > 0 ? 'var(--yellow-600)' : 'var(--text-muted)'};">${p.draft_count}</span>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-weight: 600; color: ${p.cancelled_unamended_count > 0 ? 'var(--red-500)' : 'var(--text-muted)'};">${p.cancelled_unamended_count}</span>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="color: ${severity_color}; font-weight: 600; font-size: 0.85rem;">${__(p.severity)}</span>
                    </div>
                    <div style="flex: 1; text-align: right;">
                        <button class="btn btn-default btn-xs btn-detail" data-pm="${p.party_master}" data-dt="${p.reference_doctype}">
                            ${__('View Details')}
                        </button>
                    </div>
                </div>
            `);

            row.find('.btn-detail').on('click', (e) => {
                const $btn = $(e.currentTarget);
                this.show_health_detail($btn.data('pm'), $btn.data('dt'));
            });

            content.append(row);
        });

        this.render_pagination(data.total, 'health');
    }

    show_health_detail(party_master, reference_doctype = null) {
        let title = __('Transaction Policy Issues: {0}', [party_master]);
        if (reference_doctype) {
            title = __('Transaction Policy Issues: {0} ({1})', [party_master, reference_doctype]);
        }

        const d = new frappe.ui.Dialog({
            title: title,
            size: 'large',
            fields: [
                {
                    fieldname: 'issues_html',
                    fieldtype: 'HTML'
                }
            ],
            primary_action_label: __('Close'),
            primary_action: () => d.hide()
        });

        d.fields_dict.issues_html.$wrapper.html(`<div class="text-muted text-center" style="padding: 2rem;">${__('Loading issues...')}</div>`);
        d.show();

        frappe.call({
            method: 'uph.party.controllers.transaction_health.get_party_health_detail',
            args: { party_master, reference_doctype },
            callback: (r) => {
                if (!r.message || !r.message.vouchers || !r.message.vouchers.length) {
                    d.fields_dict.issues_html.$wrapper.html(
                        `<div class="text-muted text-center" style="padding: 2rem;">${__('No problematic vouchers found for {0}', [party_master])}</div>`
                    );
                    return;
                }

                let html = `
                    <div style="display: flex; padding: 0.5rem 1rem; font-weight: 600; color: var(--text-muted); font-size: 0.85rem; border-bottom: 1px solid var(--border-color);">
                        <div style="flex: 2;">${__('Document')}</div>
                        <div style="flex: 1;">${__('Issue')}</div>
                        <div style="flex: 1;">${__('Date')}</div>
                        <div style="flex: 1.5; text-align: right;">${__('Actions')}</div>
                    </div>
                `;

                r.message.vouchers.forEach(v => {
                    let issue_color = 'gray';
                    if (v.issue_code === 'draft_overdue') issue_color = 'orange';
                    if (v.issue_code === 'cancelled_referenced') issue_color = 'red';
                    if (v.issue_code === 'party_master_mismatch') issue_color = 'blue';

                    let actions_html = '';

                    // Action logic based on docstatus and issue code
                    if (v.docstatus === 0 && v.issue_code === 'draft_overdue') {
                        actions_html += `
                            <button class="btn btn-primary btn-xs btn-action" data-action="submit" data-issue="${v.issue_name}" title="${__('Submit Document')}">
                                <i class="fa fa-check"></i> ${__('Submit')}
                            </button>
                            <button class="btn btn-default btn-xs btn-action" data-action="cancel" data-issue="${v.issue_name}" title="${__('Cancel Document')}">
                                <i class="fa fa-ban"></i>
                            </button>
                        `;
                    } else if (v.docstatus === 1 && v.issue_code === 'cancelled_referenced') {
                        actions_html += `
                            <button class="btn btn-danger btn-xs btn-action" data-action="cancel" data-issue="${v.issue_name}" title="${__('Cancel Document')}">
                                <i class="fa fa-ban"></i> ${__('Cancel')}
                            </button>
                        `;
                    }

                    // Always allow explicit dismiss from the dashboard
                    actions_html += `
                        <a href="/app/party-issue/${v.issue_name}" target="_blank" class="btn btn-default btn-xs" title="${__('Open Issue')}" style="margin-left: 4px;">
                            <i class="fa fa-external-link"></i>
                        </a>
                        <button class="btn btn-default btn-xs btn-action" data-action="dismiss" data-issue="${v.issue_name}" title="${__('Ignore Issue')}" style="margin-left: 4px;">
                            <i class="fa fa-times"></i>
                        </button>
                    `;

                    html += `
                        <div class="health-issue-row" style="display: flex; align-items: center; padding: 0.75rem 1rem; border-bottom: 1px solid var(--border-color);">
                            <div style="flex: 2;">
                                <div style="font-weight: 500;">
                                    <a href="/app/${frappe.router.slug(v.doctype)}/${v.name}" target="_blank">${v.doctype}: ${v.name}</a>
                                </div>
                                <div class="text-muted small">${v.docstatus === 0 ? 'Draft' : (v.docstatus === 1 ? 'Submitted' : 'Cancelled')}</div>
                            </div>
                            <div style="flex: 1;">
                                <span class="indicator-pill ${issue_color}">${v.issue_type}</span>
                            </div>
                            <div style="flex: 1; font-size: 0.85rem;" class="text-muted">
                                ${v.creation ? frappe.datetime.global_date_format(v.creation) : '-'}
                            </div>
                            <div style="flex: 1.5; text-align: right;">
                                ${actions_html}
                            </div>
                        </div>
                    `;
                });

                d.fields_dict.issues_html.$wrapper.html(html);

                // Bind actions
                d.fields_dict.issues_html.$wrapper.find('.btn-action').on('click', (e) => {
                    const $btn = $(e.currentTarget);
                    const action = $btn.data('action');
                    const issue = $btn.data('issue');

                    const resolve = (reason = null) => {
                        $btn.prop('disabled', true);
                        frappe.call({
                            method: 'uph.party.controllers.transaction_health.resolve_health_issue',
                            args: { issue_name: issue, action: action, reason: reason },
                            callback: (res) => {
                                if (res.message && res.message.success) {
                                    $btn.closest('.health-issue-row').fadeOut(300, function () { $(this).remove(); });
                                    frappe.show_alert({ message: res.message.message, indicator: 'green' });
                                    this.load_stats();
                                    this.load_health();
                                } else {
                                    $btn.prop('disabled', false);
                                }
                            }
                        });
                    };

                    if (action === 'dismiss') {
                        frappe.prompt({
                            label: __('Reason for Ignoring'),
                            fieldname: 'reason',
                            fieldtype: 'Small Text',
                            reqd: 1
                        }, (values) => {
                            resolve(values.reason);
                        }, __('Ignore Issue'), __('Ignore'));
                    } else {
                        let confirm_msg = '';
                        if (action === 'submit') confirm_msg = __('Are you sure you want to permanently Submit this document?');
                        if (action === 'cancel') confirm_msg = __('Are you sure you want to permanently Cancel this document?');

                        frappe.confirm(confirm_msg, () => {
                            resolve();
                        });
                    }
                });
            }
        });
    }

    // ═══════════════════════════════════════════
    // SHARED: Pagination
    // ═══════════════════════════════════════════

    render_pagination(total, tab) {
        const pagination = $('#pagination');
        pagination.empty();

        let current_offset, limit;
        if (tab === 'duplicates') {
            current_offset = this.current_offset;
            limit = this.limit;
        } else if (tab === 'unlinked') {
            current_offset = this.unlinked_offset;
            limit = this.unlinked_limit;
        } else if (tab === 'unlinked_vouchers') {
            current_offset = this.unlinked_vouchers_offset;
            limit = this.unlinked_vouchers_limit;
        } else {
            current_offset = this.health_offset;
            limit = this.health_limit;
        }

        const total_pages = Math.ceil(total / limit);
        const current_page = Math.floor(current_offset / limit) + 1;

        if (total_pages <= 1) return;

        if (current_page > 1) {
            pagination.append(`<button class="btn btn-default btn-sm btn-prev">${__('Previous')}</button>`);
        }

        pagination.append(`<span style="padding: 0 1rem;">${__('Page {0} of {1}', [current_page, total_pages])}</span>`);

        if (current_page < total_pages) {
            pagination.append(`<button class="btn btn-default btn-sm btn-next">${__('Next')}</button>`);
        }

        pagination.find('.btn-prev').on('click', () => {
            if (tab === 'duplicates') {
                this.current_offset = Math.max(0, this.current_offset - this.limit);
            } else if (tab === 'unlinked') {
                this.unlinked_offset = Math.max(0, this.unlinked_offset - this.unlinked_limit);
            } else if (tab === 'unlinked_vouchers') {
                this.unlinked_vouchers_offset = Math.max(0, this.unlinked_vouchers_offset - this.unlinked_vouchers_limit);
            } else {
                this.health_offset = Math.max(0, this.health_offset - this.health_limit);
            }
            this.load_tab_content();
        });

        pagination.find('.btn-next').on('click', () => {
            if (tab === 'duplicates') {
                this.current_offset += this.limit;
            } else if (tab === 'unlinked') {
                this.unlinked_offset += this.unlinked_limit;
            } else if (tab === 'unlinked_vouchers') {
                this.unlinked_vouchers_offset += this.unlinked_vouchers_limit;
            } else {
                this.health_offset += this.health_limit;
            }
            this.load_tab_content();
        });
    }

    // ═══════════════════════════════════════════
    // SETTINGS DIALOG
    // ═══════════════════════════════════════════

    show_settings_dialog() {
        const d = new frappe.ui.Dialog({
            title: __('Dashboard Settings'),
            fields: [
                {
                    fieldname: 'min_score',
                    fieldtype: 'Int',
                    label: __('Minimum Similarity Score'),
                    default: this.min_score,
                    description: __('Only show duplicates with similarity score above this threshold (0-100)')
                },
                {
                    fieldname: 'limit',
                    fieldtype: 'Int',
                    label: __('Results Per Page'),
                    default: this.limit
                }
            ],
            primary_action_label: __('Apply'),
            primary_action: (values) => {
                this.min_score = values.min_score;
                this.limit = values.limit;
                this.unlinked_limit = values.limit;
                this.unlinked_vouchers_limit = values.limit;
                this.health_limit = values.limit;
                this.current_offset = 0;
                this.unlinked_offset = 0;
                this.unlinked_vouchers_offset = 0;
                this.health_offset = 0;
                d.hide();
                this.load_tab_content();
            }
        });
        d.show();
    }
}
