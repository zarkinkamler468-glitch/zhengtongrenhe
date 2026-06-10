"use client";

import { useEffect, useMemo, useState } from "react";
import { Bell, Plus, Send, Trash2 } from "lucide-react";
import {
  api,
  PushChannelType,
  PushLog,
  Subscription,
  SubscriptionInput,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/lib/utils";

const PRESETS = ["职业教育", "人工智能", "双高计划", "教育数字化", "实训基地", "产教融合"];

const CHANNELS: {
  value: PushChannelType;
  label: string;
  hint: string;
  fields: { key: string; label: string; placeholder: string; secret?: boolean }[];
}[] = [
  {
    value: "email",
    label: "邮件",
    hint: "留空收件邮箱则使用账户注册邮箱；需在服务端配置 SMTP",
    fields: [{ key: "to", label: "收件邮箱", placeholder: "可选，默认用账户邮箱" }],
  },
  {
    value: "webhook",
    label: "Webhook",
    hint: 'JSON 示例：{"url":"https://your-server/hook"}',
    fields: [{ key: "url", label: "Hook URL", placeholder: "https://..." }],
  },
  {
    value: "dingtalk",
    label: "钉钉",
    hint: "钉钉群机器人 Webhook，可选加签 secret",
    fields: [
      { key: "webhook", label: "Webhook", placeholder: "https://oapi.dingtalk.com/robot/send?..." },
      { key: "secret", label: "加签密钥", placeholder: "可选", secret: true },
    ],
  },
  {
    value: "feishu",
    label: "飞书",
    hint: "飞书群自定义机器人 Webhook，可选签名校验 secret",
    fields: [
      {
        key: "webhook",
        label: "Webhook",
        placeholder: "https://open.feishu.cn/open-apis/bot/v2/hook/...",
      },
      { key: "secret", label: "签名校验密钥", placeholder: "可选", secret: true },
    ],
  },
  {
    value: "wechat_work",
    label: "企业微信",
    hint: "企业微信群机器人 Webhook 地址",
    fields: [{ key: "webhook", label: "Webhook", placeholder: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?..." }],
  },
  {
    value: "wechat_mp",
    label: "微信公众号",
    hint: "需服务端配置 WECHAT_MP_APPID/SECRET，此处填用户 openid 与模板 ID",
    fields: [
      { key: "openid", label: "用户 OpenID", placeholder: "oXXXX" },
      { key: "template_id", label: "模板 ID", placeholder: "可选，默认用服务端配置" },
    ],
  },
];

const CHANNEL_LABEL: Record<PushChannelType, string> = Object.fromEntries(
  CHANNELS.map((c) => [c.value, c.label]),
) as Record<PushChannelType, string>;

function parseConfig(raw: string | null): Record<string, string> {
  if (!raw) return {};
  try {
    const obj = JSON.parse(raw) as Record<string, string>;
    return obj && typeof obj === "object" ? obj : {};
  } catch {
    return {};
  }
}

function buildConfig(channel: PushChannelType, values: Record<string, string>): string | null {
  const meta = CHANNELS.find((c) => c.value === channel);
  if (!meta) return null;
  const config: Record<string, string> = {};
  for (const field of meta.fields) {
    const v = values[field.key]?.trim();
    if (v) config[field.key] = v;
  }
  if (channel === "webhook" && !config.url) return null;
  if (channel === "dingtalk" && !config.webhook) return null;
  if (channel === "feishu" && !config.webhook) return null;
  if (channel === "wechat_work" && !config.webhook) return null;
  if (channel === "wechat_mp" && !config.openid) return null;
  return Object.keys(config).length ? JSON.stringify(config) : null;
}

export default function SubscriptionsPage() {
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [logs, setLogs] = useState<PushLog[]>([]);
  const [keyword, setKeyword] = useState("");
  const [channel, setChannel] = useState<PushChannelType>("email");
  const [configValues, setConfigValues] = useState<Record<string, string>>({});
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  const channelMeta = useMemo(() => CHANNELS.find((c) => c.value === channel), [channel]);

  const load = () => {
    api.getSubscriptions().then(setSubs).catch(console.error);
    api.getPushLogs().then(setLogs).catch(console.error);
  };

  useEffect(() => {
    load();
  }, []);

  const formPayload = (): SubscriptionInput => ({
    keyword: keyword.trim(),
    channel,
    channel_config: buildConfig(channel, configValues),
  });

  const add = async (kw?: string) => {
    const word = (kw ?? keyword).trim();
    if (!word) return;
    setSaving(true);
    try {
      await api.createSubscription({
        keyword: word,
        channel,
        channel_config: buildConfig(channel, configValues),
      });
      setKeyword("");
      setConfigValues({});
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "添加失败");
    } finally {
      setSaving(false);
    }
  };

  const testChannel = async () => {
    setTesting(true);
    try {
      const res = await api.testPushChannel(formPayload());
      alert(res.message ?? (res.success ? "发送成功" : "发送失败"));
    } catch (e) {
      alert(e instanceof Error ? e.message : "测试失败");
    } finally {
      setTesting(false);
    }
  };

  const toggleActive = async (sub: Subscription) => {
    try {
      await api.updateSubscription(sub.id, { is_active: !sub.is_active });
      load();
    } catch {
      alert("更新失败");
    }
  };

  const remove = async (id: number) => {
    try {
      await api.deleteSubscription(id);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "";
      if (!msg.includes("订阅不存在") && !msg.includes("Not Found")) {
        alert(msg || "删除失败");
        return;
      }
    }
    load();
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary-600" />
            关键词订阅
          </CardTitle>
          <p className="text-sm text-slate-500">
            采集到新政策且标题/正文匹配关键词时，自动推送到所选渠道
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">关键词</label>
              <Input
                placeholder="如：职业教育、人工智能"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && add()}
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">推送渠道</label>
              <select
                className="h-10 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                value={channel}
                onChange={(e) => {
                  setChannel(e.target.value as PushChannelType);
                  setConfigValues({});
                }}
              >
                {CHANNELS.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {channelMeta && channelMeta.fields.length > 0 && (
            <div className="rounded-lg border border-slate-100 bg-slate-50/80 p-4">
              <p className="mb-3 text-xs text-slate-500">{channelMeta.hint}</p>
              <div className="grid gap-3 md:grid-cols-2">
                {channelMeta.fields.map((field) => (
                  <div key={field.key}>
                    <label className="mb-1 block text-xs font-medium text-slate-600">{field.label}</label>
                    <Input
                      type={field.secret ? "password" : "text"}
                      placeholder={field.placeholder}
                      value={configValues[field.key] ?? ""}
                      onChange={(e) =>
                        setConfigValues((prev) => ({ ...prev, [field.key]: e.target.value }))
                      }
                    />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            <Button onClick={() => add()} disabled={saving || !keyword.trim()}>
              <Plus className="mr-1 h-4 w-4" />
              添加订阅
            </Button>
            <Button variant="secondary" onClick={testChannel} disabled={testing}>
              <Send className="mr-1 h-4 w-4" />
              测试推送
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => add(p)}
                className="rounded-full border border-dashed border-slate-200 px-3 py-1 text-xs text-slate-600 hover:border-primary-300 hover:text-primary-600"
              >
                + {p}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>我的订阅 ({subs.length})</CardTitle>
        </CardHeader>
        <CardContent className="divide-y divide-slate-100 p-0">
          {subs.map((s) => {
            const cfg = parseConfig(s.channel_config);
            const cfgText =
              s.channel === "email"
                ? cfg.to || "账户邮箱"
                : cfg.url || cfg.webhook || cfg.openid || "—";
            return (
              <div key={s.id} className="flex flex-wrap items-center justify-between gap-3 px-6 py-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium text-slate-900">{s.keyword}</p>
                    <Badge label={s.is_active ? "启用" : "暂停"} type={s.is_active ? "active" : "inactive"} />
                  </div>
                  <p className="mt-1 truncate text-xs text-slate-500">
                    渠道：{CHANNEL_LABEL[s.channel]} · {cfgText} · {formatDate(s.created_at)}
                  </p>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => toggleActive(s)}>
                    {s.is_active ? "暂停" : "启用"}
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => remove(s.id)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            );
          })}
          {subs.length === 0 && (
            <p className="px-6 py-12 text-center text-sm text-slate-400">暂无订阅，请添加关键词</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>推送记录 ({logs.length})</CardTitle>
        </CardHeader>
        <CardContent className="divide-y divide-slate-100 p-0">
          {logs.map((log) => (
            <div key={log.id} className="flex items-start justify-between gap-3 px-6 py-3">
              <div className="min-w-0">
                <p className="truncate text-sm text-slate-800">{log.message || log.keyword}</p>
                <p className="text-xs text-slate-500">
                  {CHANNEL_LABEL[log.channel]} · 关键词 {log.keyword} · {formatDate(log.created_at)}
                </p>
              </div>
              <Badge
                label={log.status === "success" ? "成功" : "失败"}
                type={log.status === "success" ? "active" : "inactive"}
              />
            </div>
          ))}
          {logs.length === 0 && (
            <p className="px-6 py-10 text-center text-sm text-slate-400">暂无推送记录</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
