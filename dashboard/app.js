const I18N = {
  en: {
    powered_by: 'powered by commando',
    awaiting: 'Awaiting',
    running: 'Running',
    done_today: 'Done today',
    this_week: 'This week',
    today: 'Today',
    tomorrow: 'Tomorrow',
    kanban: 'Kanban',
    calendar: 'Calendar',
    table: 'Table',
    kanban_preview: 'Kanban preview',
    review: 'Review',
    waiting_review: 'Waiting review',
    done: 'Done',
    idle: 'Idle',
    inbox: 'Inbox',
    wip: 'WIP',
    review_col: 'Review',
    done_col: 'Done',
    review_btn: 'Review',
    manual_im_ready: 'Manual · IM trigger ready',
    weekday_short: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    refresh: 'Refresh',
    settings: 'Settings',
    coming_soon: 'View coming in 0.x — schedule.yaml renders only the Today view for v0.1.',
    read_from: 'reading',
    sec: 's',
    candidates: 'candidates',
    ran_at: 'ran at',
    score: 'score',
    skills: 'Skills',
    skills_active: 'Active',
    skills_draft: 'Draft',
    skills_imported: 'Imported',
    skill_tag_active: 'active',
    skill_tag_draft: 'draft',
    skill_tag_imported: 'imported',
    skill_tag_approval: 'human-approval',
    no_skills: 'no skills found in my-agent/skills/'
  },
  zh: {
    powered_by: '由 commando 驱动',
    awaiting: '待审稿',
    running: '进行中',
    done_today: '今日完成',
    this_week: '本周待办',
    today: '今日',
    tomorrow: '明日',
    kanban: '看板',
    calendar: '日历',
    table: '表格',
    kanban_preview: '看板预览',
    review: '审稿',
    waiting_review: '等你审稿',
    done: '已完成',
    idle: '空闲',
    inbox: '待处理',
    wip: '进行中',
    review_col: '待审',
    done_col: '已完成',
    review_btn: '审稿',
    manual_im_ready: '手动 · IM 触发待命',
    weekday_short: ['日', '一', '二', '三', '四', '五', '六'],
    refresh: '刷新',
    settings: '设置',
    coming_soon: '此视图在 0.x 阶段尚未启用 —— v0.1 仅渲染 Today 视图。',
    read_from: '读自',
    sec: '秒',
    candidates: '条候选',
    ran_at: '跑于',
    score: '分',
    skills: '技能',
    skills_active: '激活',
    skills_draft: '草稿',
    skills_imported: '从 Registry 导入',
    skill_tag_active: 'active',
    skill_tag_draft: 'draft',
    skill_tag_imported: 'imported',
    skill_tag_approval: '需人审',
    no_skills: 'my-agent/skills/ 下没有发现 Skill'
  }
};

function detectLang() {
  const saved = localStorage.getItem('commando.lang');
  if (saved) return saved;
  return (navigator.language || 'en').toLowerCase().startsWith('zh') ? 'zh' : 'en';
}

function detectTheme() {
  return localStorage.getItem('commando.theme') || 'auto';
}

function applyTheme(mode) {
  const root = document.documentElement;
  if (mode === 'auto') {
    root.removeAttribute('data-theme');
  } else {
    root.setAttribute('data-theme', mode);
  }
}

function dashboard() {
  return {
    lang: detectLang(),
    theme: detectTheme(),
    activeTab: 'today',
    data: null,
    loading: true,
    error: null,

    async init() {
      applyTheme(this.theme);
      await this.load();
    },

    async load() {
      this.loading = true;
      this.error = null;
      try {
        const r = await fetch('/api/data');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        this.data = await r.json();
      } catch (e) {
        this.data = STATIC_MOCK;
      } finally {
        this.loading = false;
      }
    },

    t(key) {
      return (I18N[this.lang] && I18N[this.lang][key]) || I18N.en[key] || key;
    },

    weekday(dateStr) {
      const d = new Date(dateStr + 'T00:00:00');
      return this.t('weekday_short')[d.getDay()];
    },

    dateLabel(dateStr) {
      const d = new Date(dateStr + 'T00:00:00');
      const m = d.getMonth() + 1;
      const day = d.getDate();
      return this.weekday(dateStr) + ' ' + m + '/' + day;
    },

    toggleLang() {
      this.lang = this.lang === 'zh' ? 'en' : 'zh';
      localStorage.setItem('commando.lang', this.lang);
    },

    cycleTheme() {
      const next = { auto: 'light', light: 'dark', dark: 'auto' };
      this.theme = next[this.theme];
      localStorage.setItem('commando.theme', this.theme);
      applyTheme(this.theme);
    },

    themeIcon() {
      return { auto: 'ti-device-desktop', light: 'ti-sun', dark: 'ti-moon' }[this.theme];
    },

    pillClass(status) {
      const map = {
        Done: 'pill pill-done',
        WaitingApproval: 'pill pill-ask',
        Running: 'pill pill-wip',
        WIP: 'pill pill-wip',
        Idle: 'pill pill-idle',
        Manual: 'pill pill-idle'
      };
      return map[status] || 'pill pill-idle';
    },

    pillLabel(status) {
      const map = {
        Done: this.t('done'),
        WaitingApproval: this.t('waiting_review'),
        Running: this.t('wip'),
        WIP: this.t('wip'),
        Idle: this.t('idle'),
        Manual: this.t('idle')
      };
      return map[status] || status;
    },

    pillIcon(status) {
      const map = {
        Done: 'ti-check',
        WaitingApproval: 'ti-clock',
        Running: 'ti-player-play',
        WIP: 'ti-player-play',
        Idle: '',
        Manual: ''
      };
      return map[status] || '';
    },

    isAsk(t) {
      return t.status === 'WaitingApproval';
    },

    async openArtifact(task) {
      if (!task.artifact_uri) return;
      if (task.artifact_uri.startsWith('file://')) {
        await fetch('/api/open?uri=' + encodeURIComponent(task.artifact_uri));
      } else {
        window.open(task.artifact_uri, '_blank', 'noopener');
      }
    },

    skillTagClass(s) {
      if (s.status === 'draft') return 'skill-tag skill-tag-draft';
      if (s.status === 'imported-placeholder' || s.source) return 'skill-tag skill-tag-imported';
      return 'skill-tag skill-tag-active';
    },

    skillTagLabel(s) {
      if (s.status === 'draft') return this.t('skill_tag_draft');
      if (s.status === 'imported-placeholder' || s.source) return this.t('skill_tag_imported');
      return this.t('skill_tag_active');
    },

    skillsGrouped() {
      const arr = (this.data && this.data.skills) || [];
      const imported = [];
      const drafts = [];
      const actives = [];
      for (const s of arr) {
        if (s.status === 'draft') drafts.push(s);
        else if (s.status === 'imported-placeholder' || s.source) imported.push(s);
        else actives.push(s);
      }
      return { actives, imported, drafts };
    }
  };
}

const STATIC_MOCK = {
  agent: { name: '阿土', subtitle: 'LeMingle 增长合伙人', avatar: '阿' },
  metrics: { awaiting: 1, running: 2, done_today: 4, this_week: 9 },
  today: {
    date: '2026-06-11',
    tasks: [
      {
        id: 'morning_sense-1',
        task_id: 'morning_sense',
        skills: ['reddit-source-mining', 'outlet-rss-scan'],
        status: 'Done',
        summary: '08:00 ran · 12 candidates · 142s',
        artifact_uri: null
      },
      {
        id: 'xhs_draft_tue-1',
        task_id: 'xhs_draft_tue',
        skills: ['xhs-bilingual-bridge'],
        status: 'WaitingApproval',
        summary: '11:00 ran · 1 笔记初稿 · 等你审稿',
        artifact_uri: 'file:///mock/draft-xhs-tue.md'
      },
      {
        id: 'user_call_prep-idle',
        task_id: 'user_call_prep',
        skills: ['user-call-prep'],
        status: 'Manual',
        summary: 'Manual · IM trigger ready',
        artifact_uri: null
      }
    ]
  },
  tomorrow: {
    date: '2026-06-12',
    tasks: [
      { id: 't1', task_id: 'morning_sense', time: '08:00' },
      { id: 't2', task_id: 'xhs_draft_thu', time: '11:00' },
      { id: 't3', task_id: 'user_call_prep', time: '14:30' },
      { id: 't4', task_id: 'daily_journal', time: '17:00' }
    ]
  },
  kanban: {
    inbox: [{ title: 'idiom passively', meta: 'score 4.3' }],
    wip: [{ title: 'xhs_draft_tue', meta: '11:02 ago' }],
    review: [{ title: 'circle back note', meta: '11:02 done' }],
    done: [{ title: 'morning_sense', meta: '08:00 · 12 picked' }]
  }
};

window.dashboard = dashboard;

document.addEventListener('alpine:init', () => {
  window.Alpine.data('dashboard', dashboard);
});
