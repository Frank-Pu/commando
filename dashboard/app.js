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
    no_skills: 'no skills found in my-agent/skills/',
    knowledge: 'Knowledge',
    knowledge_subtitle: "this agent's plans / drafts / data / user quotes",
    open_in: 'open in {backend}',
    open_all: 'open all',
    switch_agent: 'switch agent',
    items_total: '· {n} items',
    activity: 'Live',
    activity_subtitle: 'real-time agent action stream',
    live: 'live',
    events_today: '{n} events today',
    just_now: 'just now',
    minutes_ago: '{n}m ago',
    yesterday: 'yest',
    pause: 'pause',
    resume: 'resume',
    lvl_trigger: 'TRIG',
    lvl_running: 'RUN',
    lvl_done: 'DONE',
    lvl_waiting: 'WAIT',
    lvl_idle: 'IDLE',
    lvl_im: 'IM',
    close: 'Close',
    kanban_subtitle: 'tasks across status',
    calendar_note: 'Tasks are derived from cron expressions in schedule.yaml; the agent fires them automatically — you only see them here.',
    weekday_long: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    view_week: 'Week',
    view_month: 'Month',
    more_n: '+{n} more'
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
    no_skills: 'my-agent/skills/ 下没有发现 Skill',
    knowledge: '知识库',
    knowledge_subtitle: '此 agent 记录的方案 / 文案 / 数据 / 用户原话',
    open_in: '在 {backend} 打开',
    open_all: '全部打开',
    switch_agent: '切换 agent',
    items_total: '· {n} 条',
    activity: '实况',
    activity_subtitle: 'agent 实时行动流',
    live: '在线',
    events_today: '今日 {n} 条',
    just_now: '刚刚',
    minutes_ago: '{n} 分钟前',
    yesterday: '昨天',
    pause: '暂停',
    resume: '继续',
    lvl_trigger: '触发',
    lvl_running: '运行',
    lvl_done: '完成',
    lvl_waiting: '待审',
    lvl_idle: '空闲',
    lvl_im: '私信',
    close: '关闭',
    kanban_subtitle: '按状态切分',
    calendar_note: '日程是从 schedule.yaml 的 cron 表达式推算的；agent 会自动触发，你只是看到。',
    weekday_long: ['周日', '周一', '周二', '周三', '周四', '周五', '周六'],
    view_week: '周',
    view_month: '月',
    more_n: '+{n} 更多'
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
    calendarView: 'week',
    showSkills: false,
    agents: [],
    activeAgentId: null,
    agentMenuOpen: false,
    data: null,
    loading: true,
    error: null,
    nowClock: '',
    liveEvents: [],
    livePaused: false,
    _liveTimer: null,
    _clockTimer: null,
    _liveSeedIdx: 0,

    async init() {
      applyTheme(this.theme);
      await this.loadAgents();
      await this.load();
      this.startClock();
      this.startLive();
    },

    startClock() {
      const tick = () => {
        const d = new Date();
        const pad = (n) => String(n).padStart(2, '0');
        this.nowClock = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
      };
      tick();
      if (this._clockTimer) clearInterval(this._clockTimer);
      this._clockTimer = setInterval(tick, 1000);
    },

    startLive() {
      if (this._liveTimer) clearInterval(this._liveTimer);
      this._liveSeedIdx = 0;
      this._liveTimer = setInterval(() => {
        if (this.livePaused) return;
        if (this.activeTab !== 'activity') return;
        this.injectLiveEvent();
      }, 9000);
    },

    injectLiveEvent() {
      const seeds = (this.data && this.data.activity && this.data.activity.live_seeds) || [];
      if (!seeds.length) return;
      const seed = seeds[this._liveSeedIdx % seeds.length];
      this._liveSeedIdx++;
      const ev = Object.assign({}, seed, {
        ts: new Date().toISOString(),
        _id: 'live-' + Date.now(),
        _fresh: true,
      });
      this.liveEvents = [ev, ...this.liveEvents].slice(0, 40);
      setTimeout(() => { ev._fresh = false; }, 4000);
    },

    toggleLive() { this.livePaused = !this.livePaused; },

    allEvents() {
      const historical = (this.data && this.data.activity && this.data.activity.events) || [];
      return [...this.liveEvents, ...historical].slice(0, 80);
    },

    eventsTodayCount() {
      const all = this.allEvents();
      const today = new Date().toDateString();
      return all.filter(e => new Date(e.ts).toDateString() === today).length;
    },

    formatTs(ts) {
      const d = new Date(ts);
      const now = new Date();
      const diffSec = Math.floor((now - d) / 1000);
      if (diffSec < 60) return this.t('just_now');
      if (diffSec < 3600) return this.t('minutes_ago').replace('{n}', Math.floor(diffSec / 60));
      const pad = (n) => String(n).padStart(2, '0');
      const sameDay = d.toDateString() === now.toDateString();
      const yest = new Date(now); yest.setDate(now.getDate() - 1);
      const isYest = d.toDateString() === yest.toDateString();
      const hhmm = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
      if (sameDay) return hhmm;
      if (isYest) return this.t('yesterday') + ' ' + hhmm.slice(0, 5);
      return (d.getMonth() + 1) + '/' + d.getDate() + ' ' + hhmm.slice(0, 5);
    },

    formatDuration(ms) {
      if (!ms) return '';
      if (ms < 1000) return ms + 'ms';
      const s = Math.round(ms / 1000);
      if (s < 60) return s + 's';
      return Math.floor(s / 60) + 'm' + (s % 60) + 's';
    },

    lvlLabel(lvl) {
      return this.t('lvl_' + lvl) || lvl;
    },

    lvlClass(lvl) {
      return 'lvl lvl-' + lvl;
    },

    async loadAgents() {
      try {
        const r = await fetch('/api/agents');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const j = await r.json();
        this.agents = j.agents || [];
        const saved = localStorage.getItem('commando.activeAgent');
        if (saved && this.agents.some(a => a.id === saved)) {
          this.activeAgentId = saved;
        } else {
          this.activeAgentId = j.active_id || (this.agents[0] && this.agents[0].id);
        }
      } catch (e) {
        this.agents = [
          {id: 'atu', name: '阿土', subtitle: 'LeMingle 增长合伙人', avatar: '阿'},
          {id: 'caiwa', name: '财娃', subtitle: '投研助手 · A 股 + 港股', avatar: '财'},
        ];
        this.activeAgentId = 'atu';
      }
    },

    async load() {
      this.loading = true;
      this.error = null;
      try {
        const url = this.activeAgentId ? '/api/data?agent=' + encodeURIComponent(this.activeAgentId) : '/api/data';
        const r = await fetch(url);
        if (!r.ok) throw new Error('HTTP ' + r.status);
        this.data = await r.json();
      } catch (e) {
        this.data = STATIC_MOCK;
      } finally {
        this.loading = false;
      }
    },

    async switchAgent(id) {
      if (id === this.activeAgentId) {
        this.agentMenuOpen = false;
        return;
      }
      this.activeAgentId = id;
      localStorage.setItem('commando.activeAgent', id);
      this.agentMenuOpen = false;
      this.activeTab = 'today';
      this.liveEvents = [];
      this._liveSeedIdx = 0;
      await this.load();
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

    openLink(url) {
      if (!url || url === '#') return;
      window.open(url, '_blank', 'noopener');
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

    weekdayLong(idx) {
      const arr = (I18N[this.lang] && I18N[this.lang].weekday_long) || I18N.en.weekday_long;
      return arr[idx] || '';
    },

    weekdayHeaders() {
      const arr = (I18N[this.lang] && I18N[this.lang].weekday_long) || I18N.en.weekday_long;
      return arr;
    },

    monthLabel() {
      if (!this.data || !this.data.month) return '';
      return this.lang === 'zh' ? this.data.month.month_zh : this.data.month.label;
    },

    moreLabel(n) {
      return this.t('more_n').replace('{n}', n);
    },

    knowledgeCategoryName(c) {
      return this.lang === 'zh' ? (c.name_zh || c.name_en) : (c.name_en || c.name_zh);
    },

    knowledgeItemUpdated(it) {
      return this.lang === 'zh' ? (it.updated_zh || it.updated_en) : (it.updated_en || it.updated_zh);
    },

    openInLabel(backend) {
      return this.t('open_in').replace('{backend}', backend);
    },

    itemsTotalLabel(n) {
      return this.t('items_total').replace('{n}', n);
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
