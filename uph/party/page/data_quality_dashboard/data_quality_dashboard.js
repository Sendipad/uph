frappe.pages['data-quality-dashboard'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Data Quality Dashboard'),
        single_column: true
    });

    // Store page reference
    page.main.addClass('data-quality-dashboard');

    // Initialize dashboard
    new DataQualityDashboard(page);
};

class DataQualityDashboard {
    constructor(page) {
        this.page = page;
        this.wrapper = $(page.main);
        this.current_offset = 0;
        this.limit = 20;
        this.min_score = 70;

        this.init();
    }

    init() {
        this.setup_page_actions();
        this.render_layout();
        this.load_stats();
        this.load_duplicates();
    }

    setup_page_actions() {
        // Refresh button
        this.page.set_primary_action(__('Refresh'), () => {
            this.load_stats();
            this.load_duplicates();
        }, 'refresh');

        // Settings button
        this.page.add_menu_item(__('Settings'), () => {
            this.show_settings_dialog();
        });
    }

    render_layout() {
        this.wrapper.html(`
            <div class="data-quality-container">
                <!-- Stats Cards -->
                <div class="stats-row" style="display: flex; gap: 1rem; margin-bottom: 2rem; flex-wrap: wrap;">
                    <div class="stat-card" id="stat-total-parties" style="flex: 1; min-width: 150px; padding: 1rem; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow-sm);">
                        <div class="stat-value" style="font-size: 2rem; font-weight: 600;">-</div>
                        <div class="stat-label" style="color: var(--text-muted);">${__('Total Parties')}</div>
                    </div>
                    <div class="stat-card" id="stat-potential-dups" style="flex: 1; min-width: 150px; padding: 1rem; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow-sm);">
                        <div class="stat-value" style="font-size: 2rem; font-weight: 600; color: var(--orange-500);">-</div>
                        <div class="stat-label" style="color: var(--text-muted);">${__('Potential Duplicates')}</div>
                    </div>
                    <div class="stat-card" id="stat-incomplete" style="flex: 1; min-width: 150px; padding: 1rem; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow-sm);">
                        <div class="stat-value" style="font-size: 2rem; font-weight: 600; color: var(--yellow-500);">-</div>
                        <div class="stat-label" style="color: var(--text-muted);">${__('Incomplete Records')}</div>
                    </div>
                    <div class="stat-card" id="stat-exclusions" style="flex: 1; min-width: 150px; padding: 1rem; background: var(--card-bg); border-radius: 8px; box-shadow: var(--shadow-sm);">
                        <div class="stat-value" style="font-size: 2rem; font-weight: 600; color: var(--green-500);">-</div>
                        <div class="stat-label" style="color: var(--text-muted);">${__('Dismissed Pairs')}</div>
                    </div>
                </div>

                <!-- Duplicates List -->
                <div class="duplicates-section">
                    <h3 style="margin-bottom: 1rem;">${__('Potential Duplicates')}</h3>
                    <div class="duplicates-list" id="duplicates-list">
                        <div class="text-muted">${__('Loading...')}</div>
                    </div>
                    <div class="pagination-controls" id="pagination" style="margin-top: 1rem; display: flex; gap: 0.5rem; justify-content: center;"></div>
                </div>
            </div>
        `);
    }

    load_stats() {
        frappe.call({
            method: 'uph.party.page.data_quality_dashboard.data_quality_dashboard.get_dashboard_stats',
            callback: (r) => {
                if (r.message) {
                    this.update_stats(r.message);
                }
            }
        });
    }

    update_stats(stats) {
        $('#stat-total-parties .stat-value').text(stats.total_parties || 0);
        $('#stat-potential-dups .stat-value').text(stats.potential_duplicates || 0);
        $('#stat-incomplete .stat-value').text(stats.incomplete_parties || 0);
        $('#stat-exclusions .stat-value').text(stats.total_exclusions || 0);
    }

    load_duplicates() {
        frappe.call({
            method: 'uph.party.page.data_quality_dashboard.data_quality_dashboard.get_potential_duplicates',
            args: {
                limit: this.limit,
                offset: this.current_offset,
                min_score: this.min_score
            },
            callback: (r) => {
                if (r.message) {
                    this.render_duplicates(r.message);
                }
            }
        });
    }

    render_duplicates(data) {
        const list = $('#duplicates-list');
        list.empty();

        if (!data.duplicates || data.duplicates.length === 0) {
            list.html(`<div class="text-muted text-center" style="padding: 2rem;">${__('No potential duplicates found')}</div>`);
            return;
        }

        data.duplicates.forEach((dup, idx) => {
            const card = $(`
                <div class="duplicate-card" style="background: var(--card-bg); border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: var(--shadow-sm);">
                    <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 1rem;">
                        <div style="flex: 1; min-width: 200px;">
                            <div style="font-weight: 600;">
                                <a href="/app/party-master/${dup.party_1.name}" target="_blank">${dup.party_1.party_name}</a>
                            </div>
                            <div class="text-muted small">${dup.party_1.party_type || ''} | ${dup.party_1.party_number || '-'}</div>
                        </div>
                        <div style="text-align: center; padding: 0 1rem;">
                            <div class="similarity-badge" style="background: ${this.get_score_color(dup.similarity_score)}; color: white; padding: 0.25rem 0.75rem; border-radius: 1rem; font-weight: 600;">
                                ${dup.similarity_score}%
                            </div>
                            <div class="text-muted small" style="margin-top: 0.25rem;">${__('Similarity')}</div>
                        </div>
                        <div style="flex: 1; min-width: 200px; text-align: right;">
                            <div style="font-weight: 600;">
                                <a href="/app/party-master/${dup.party_2.name}" target="_blank">${dup.party_2.party_name}</a>
                            </div>
                            <div class="text-muted small">${dup.party_2.party_type || ''} | ${dup.party_2.party_number || '-'}</div>
                        </div>
                    </div>
                    <div style="margin-top: 1rem; display: flex; gap: 0.5rem; justify-content: flex-end;">
                        <button class="btn btn-default btn-sm btn-dismiss" data-party1="${dup.party_1.name}" data-party2="${dup.party_2.name}">
                            ${__('Not a Duplicate')}
                        </button>
                        <button class="btn btn-primary btn-sm btn-merge" data-party1="${dup.party_1.name}" data-party2="${dup.party_2.name}">
                            ${__('Merge')}
                        </button>
                    </div>
                </div>
            `);

            // Bind button events
            card.find('.btn-dismiss').on('click', (e) => {
                const $btn = $(e.currentTarget);
                this.dismiss_duplicate($btn.data('party1'), $btn.data('party2'));
            });

            card.find('.btn-merge').on('click', (e) => {
                const $btn = $(e.currentTarget);
                this.show_merge_dialog($btn.data('party1'), $btn.data('party2'));
            });

            list.append(card);
        });

        // Render pagination
        this.render_pagination(data.total);
    }

    get_score_color(score) {
        if (score >= 90) return 'var(--red-500)';
        if (score >= 80) return 'var(--orange-500)';
        return 'var(--yellow-600)';
    }

    render_pagination(total) {
        const pagination = $('#pagination');
        pagination.empty();

        const total_pages = Math.ceil(total / this.limit);
        const current_page = Math.floor(this.current_offset / this.limit) + 1;

        if (total_pages <= 1) return;

        // Previous button
        if (current_page > 1) {
            pagination.append(`<button class="btn btn-default btn-sm btn-prev">${__('Previous')}</button>`);
        }

        pagination.append(`<span style="padding: 0 1rem;">${__('Page {0} of {1}', [current_page, total_pages])}</span>`);

        // Next button
        if (current_page < total_pages) {
            pagination.append(`<button class="btn btn-default btn-sm btn-next">${__('Next')}</button>`);
        }

        // Bind events
        pagination.find('.btn-prev').on('click', () => {
            this.current_offset = Math.max(0, this.current_offset - this.limit);
            this.load_duplicates();
        });

        pagination.find('.btn-next').on('click', () => {
            this.current_offset += this.limit;
            this.load_duplicates();
        });
    }

    dismiss_duplicate(party1, party2) {
        frappe.prompt({
            label: __('Reason (optional)'),
            fieldname: 'reason',
            fieldtype: 'Small Text'
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
                this.current_offset = 0;
                d.hide();
                this.load_duplicates();
            }
        });
        d.show();
    }
}
