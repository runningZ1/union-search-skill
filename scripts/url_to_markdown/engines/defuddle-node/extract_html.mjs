// 常驻提取进程：node extract_html.mjs
// 从 stdin 逐行读取 {"html": "...", "url": "..."}，对每行输出一行 JSON 结果。
// 页面由调用方下载并解码；JSDOM 与 Defuddle 只在进程启动时加载一次，之后每页只做解析与转换。
import { readFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { createInterface } from 'node:readline';
import { JSDOM, VirtualConsole } from 'jsdom';
import { Defuddle } from 'defuddle/node';

// jsdom 版本固定为 package.json 中的 24.1.3，这里使用它的内部包装函数
const { implForWrapper, wrapperForImpl } = createRequire(import.meta.url)('jsdom/lib/jsdom/living/generated/utils.js');

// jsdom 的 HTMLCollection 是 Proxy，每次按名称读取属性（包括每一步迭代读取的 length）都会遍历整个集合，
// Array.from(document.getElementsByTagName('*')) 因此是平方复杂度。这里按标准数组迭代器的语义
// （每一步重新读取当前长度、按序号取元素）直接读取内部列表，结果与原生迭代相同。
function fastCollectionIterator(window) {
  window.HTMLCollection.prototype[Symbol.iterator] = function* () {
    const impl = implForWrapper(this);
    for (let index = 0; ; index++) {
      impl._update();
      if (index >= impl._list.length) return;
      yield wrapperForImpl(impl._list[index]);
    }
  };
}

// defuddle 的 exports 不包含 package.json，按安装位置读取版本
const packageFile = new URL('./node_modules/defuddle/package.json', import.meta.url);
const { version } = JSON.parse(await readFile(packageFile, 'utf-8'));
const extractor = `defuddle@${version}`;

async function extract(html, pageUrl) {
  // 页面 CSS 解析告警与正文无关，不写入输出
  const dom = new JSDOM(html, { url: pageUrl, virtualConsole: new VirtualConsole() });
  fastCollectionIterator(dom.window);
  try {
    const result = await Defuddle(dom, pageUrl, { markdown: true });
    return {
      extractor,
      content: result.content,
      title: result.title,
      description: result.description,
      domain: result.domain,
      author: result.author,
      published: result.published,
      site: result.site,
      image: result.image,
      wordCount: result.wordCount,
      extractorType: result.extractorType ?? null,
      schemaOrgData: result.schemaOrgData ?? null,
    };
  } finally {
    // 释放页面对象，常驻进程内存不随处理页数增长
    dom.window.close();
  }
}

// 调用方每个进程同时只发一个请求，逐行顺序处理
const lines = createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of lines) {
  const request = JSON.parse(line);
  let reply;
  try {
    reply = { ok: true, result: await extract(request.html, request.url) };
  } catch (error) {
    reply = { ok: false, error: String(error && error.stack ? error.stack : error) };
  }
  process.stdout.write(JSON.stringify(reply) + '\n');
}
