def upload(results, date_str, retries=3):
    url, key = load_config()
    if not url or not key:
        print("[错误] 未找到 Supabase 配置")
        print(f"       请在 {os.path.join(SCRIPT_DIR, 'supabase_config.json')} 中填写:")
        print('       {"url": "https://xxx.supabase.co", "key": "你的service_role_key"}')
        return False

    code_str = "|".join(f"{m}:{results[m]}" for m in MAPS)
    api = f"{url}/rest/v1/daily_codes"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        # 关键：冲突时按 code_date 合并（upsert）
        "Prefer": "resolution=merge-duplicates,on_conflict=code_date,return=minimal",
    }
    data = [{
        "code_date": date_str,
        "code_value": code_str,
        "verified": True,
        "source": "wegame-quickfill",
    }]

    for attempt in range(1, retries + 1):
        try:
            r = requests.post(api, headers=headers, json=data, timeout=20)
            if r.status_code in (200, 201, 204):
                print(f"[成功] 已写入 Supabase (第{attempt}次尝试)")
                print(f"       {date_str}: {code_str}")
                return True
            if r.status_code == 409:
                # upsert 不可用 -> 降级为 PATCH 更新
                print("  [409] 已存在，改用 PATCH 更新...")
                u = f"{api}?code_date=eq.{date_str}"
                h2 = dict(headers)
                h2["Prefer"] = "return=minimal"
                r2 = requests.patch(u, headers=h2, json=data[0], timeout=20)
                if r2.status_code in (200, 201, 204):
                    print(f"[成功] 已更新 Supabase")
                    print(f"       {date_str}: {code_str}")
                    return True
                print(f"  [警告] PATCH HTTP {r2.status_code}: {r2.text[:200]}")
            else:
                print(f"[警告] HTTP {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"[警告] 第{attempt}次失败: {type(e).__name__}，重试中...")
    print("[失败] 上传最终失败，请检查网络或 Supabase 项目是否暂停")
    return False