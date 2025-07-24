frappe.provide('uph.hub');
frappe.require([
  'https://unpkg.com/vue@3/dist/vue.global.prod.js',
  'https://unpkg.com/vue3-sfc-loader'
], () => {
  const { loadModule } = window['vue3-sfc-loader'];
  const fileMap = {
    RuleBuilder: '/assets/uph/js/components/RuleBuilder.vue',
    ActionBuilder: '/assets/uph/js/components/RuleActionBuilder.vue'
  };

  // mount condition builder
  const condTarget = document.getElementById('rule-conditions');
  if (condTarget) {
    loadModule(fileMap.RuleBuilder, {
      moduleCache: { vue: Vue },
      getFile: url => fetch(url).then(r => r.text()),
      addStyle: str => {
        const tag = document.createElement('style'); tag.textContent = str; document.head.appendChild(tag);
      }
    }).then(module => {
      Vue.createApp(module.default, {
        docname: cur_frm.doc.name,
        doctype: cur_frm.doctype,
        meta: cur_frm.meta,
        table: 'conditions',
        childType: 'Rule Condition'
      }).mount(condTarget);
    });
  }

  // mount action builder
  const actTarget = document.getElementById('rule-actions');
  if (actTarget) {
    loadModule(fileMap.ActionBuilder, {
      moduleCache: { vue: Vue },
      getFile: url => fetch(url).then(r => r.text()),
      addStyle: str => {
        const tag = document.createElement('style'); tag.textContent = str; document.head.appendChild(tag);
      }
    }).then(module => {
      Vue.createApp(module.default, {
        docname: cur_frm.doc.name,
        doctype: cur_frm.doctype,
        meta: cur_frm.meta,
        table: 'actions',
        childType: 'Rule Action'
      }).mount(actTarget);
    });
  }
});
