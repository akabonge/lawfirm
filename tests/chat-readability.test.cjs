const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

// Exercise the real send/receive path with a small DOM double and no network.
async function receive(response, question = 'What services do you offer?') {
  const nodes = [];
  const htmlWrites = [];
  function element(tagName) {
    const node = {
      tagName, children: [], style: {}, value: '', scrollHeight: 100,
      classList: { add() {}, remove() {}, toggle() {} },
      addEventListener() {},
      appendChild(child) { child.parent = this; this.children.push(child); return child; },
      remove() { this.parent.children = this.parent.children.filter(child => child !== this); },
      set textContent(value) { this.children = [{ tagName: '#text', textContent: String(value) }]; },
      get textContent() { return this.children.map(child => child.textContent).join(''); },
      set innerHTML(value) { htmlWrites.push({ node: this, value }); },
    };
    nodes.push(node);
    return node;
  }
  const input = element('textarea');
  input.id = 'chat-input';
  input.value = question;
  const messages = element('div');
  messages.id = 'chat-messages';
  const context = {
    window: {},
    document: {
      getElementById: id => nodes.find(node => node.id === id),
      createElement: element,
      createTextNode: text => ({ tagName: '#text', textContent: text }),
    },
    speechSynthesis: { getVoices: () => [], cancel() {}, speak() {} },
    SpeechSynthesisUtterance: class { constructor(text) { this.text = text; } },
    fetch: async () => ({ json: async () => ({ response }) }),
  };
  const source = fs.readFileSync(path.join(__dirname, '../frontend/static/app.js'), 'utf8');
  vm.runInNewContext(source, context);
  await context.window.sendMessage();
  return {
    bot: messages.children.find(node => node.className === 'msg bot'),
    user: messages.children.find(node => node.className === 'msg user'),
    htmlWrites,
  };
}

test('preserves numbered paragraphs and line breaks while emphasizing paired bold text', async () => {
  const text = 'Our practice areas:\n\n1. **Personal Injury** — advice.\n\n2. **Family Law** — support.\nNext line.';
  const { bot } = await receive(text);
  assert.equal(bot.textContent, 'Our practice areas:\n\n1. Personal Injury — advice.\n\n2. Family Law — support.\nNext line.');
  assert.deepEqual(bot.children.filter(node => node.tagName === 'strong').map(node => node.textContent), ['Personal Injury', 'Family Law']);
});

test('leaves unmatched markers, unsupported Markdown and cross-line pairs literal', async () => {
  const text = '**unfinished\n**two\nlines**\n****\n[link](https://example.com)\n*italic*';
  const { bot } = await receive(text);
  assert.equal(bot.textContent, text);
  assert.equal(bot.children.some(node => node.tagName !== '#text'), false);
});

test('treats HTML and entities as text, including inside paired bold markers', async () => {
  const text = '<img src=x onerror="alert(1)">\n\n**<script>alert(2)</script>** &lt;b&gt;';
  const { bot, htmlWrites } = await receive(text);
  assert.equal(bot.textContent, '<img src=x onerror="alert(1)">\n\n<script>alert(2)</script> &lt;b&gt;');
  assert.deepEqual(bot.children.filter(node => node.tagName !== '#text').map(node => node.tagName), ['strong']);
  assert.equal(bot.children.find(node => node.tagName === 'strong').children[0].tagName, '#text');
  assert.equal(htmlWrites.some(write => write.node === bot), false);
});

test('keeps user messages literal and handles an ordinary assistant reply unchanged', async () => {
  const { bot, user } = await receive('Hello — how can I help?', '**my message** <b>literal</b>');
  assert.equal(bot.textContent, 'Hello — how can I help?');
  assert.equal(user.textContent, '**my message** <b>literal</b>');
});
