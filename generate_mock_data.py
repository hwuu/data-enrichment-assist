import sqlite3
import json
import random
from datetime import datetime, timedelta

# 连接数据库（如果不存在会自动创建）
conn = sqlite3.connect('gaussdb_ops.db')
cursor = conn.cursor()

# 创建 ticket_classification_2512 表
cursor.execute('''
CREATE TABLE IF NOT EXISTS ticket_classification_2512 (
    "processId" TEXT PRIMARY KEY,
    "issueType" TEXT,
    "owner" TEXT
)
''')

# 创建 operations_kb 表
cursor.execute('''
CREATE TABLE IF NOT EXISTS operations_kb (
    "流程ID" TEXT PRIMARY KEY,
    "create_time" TEXT,
    "update_time" TEXT,
    "问题现象" TEXT,
    "问题根因" TEXT,
    "分析过程" TEXT,
    "解决方案" TEXT,
    "diff_score" REAL,
    "得分" REAL,
    "理由" TEXT,
    FOREIGN KEY ("流程ID") REFERENCES ticket_classification_2512("processId")
)
''')

# 模拟数据
issue_types = ['慢SQL', '备份恢复', '日志管理']
owners = ['张三', '李四', '王五', '赵六', '钱七']

# 针对不同 issueType 的模拟数据模板
templates = {
    '慢SQL': {
        '问题现象': [
            '客户反馈业务查询响应时间超过30秒，影响正常业务运行',
            '数据库CPU使用率持续90%以上，大量查询堆积',
            '某核心业务表查询耗时从毫秒级升至分钟级',
            '批量报表生成任务执行超时，无法正常完成'
        ],
        '问题根因': [
            '索引缺失导致全表扫描，表数据量达到千万级',
            'SQL语句未使用绑定变量，导致硬解析过多',
            '统计信息过期，优化器选择了错误的执行计划',
            '存在笛卡尔积，多表关联条件缺失'
        ],
        '分析过程': [
            [
                {'操作': '查看慢SQL日志', '现象': '发现多条执行时间超过10秒的SQL', '现象分析': '存在性能问题的SQL需要优化'},
                {'操作': '执行EXPLAIN分析', '现象': 'type为ALL，rows预估值很大', '现象分析': '发生了全表扫描'},
                {'操作': '检查索引情况', '现象': 'WHERE条件字段无索引', '现象分析': '缺少必要索引是根因'},
                {'操作': '查看表统计信息', '现象': '统计信息更新时间为3个月前', '现象分析': '统计信息过期可能影响执行计划'}
            ],
            [
                {'操作': '监控数据库负载', '现象': 'CPU使用率95%，等待事件主要是CPU', '现象分析': '存在CPU密集型操作'},
                {'操作': '查询活跃会话', '现象': '发现20+会话执行相同SQL', '现象分析': '热点SQL需要优化'},
                {'操作': '分析执行计划', '现象': '嵌套循环次数过多', '现象分析': '关联方式不当导致性能问题'}
            ]
        ],
        '解决方案': [
            [
                {'描述': '创建复合索引', '具体命令': 'CREATE INDEX idx_order_customer_date ON orders(customer_id, order_date);'},
                {'描述': '更新统计信息', '具体命令': 'ANALYZE TABLE orders;'},
                {'描述': '验证优化效果', '具体命令': 'EXPLAIN SELECT * FROM orders WHERE customer_id = 1001;'}
            ],
            [
                {'描述': '改写SQL语句', '具体命令': 'SELECT /*+ USE_HASH(a,b) */ a.*, b.name FROM table_a a JOIN table_b b ON a.id = b.aid;'},
                {'描述': '添加绑定变量', '具体命令': 'PREPARE stmt FROM "SELECT * FROM users WHERE id = ?";'}
            ]
        ]
    },
    '备份恢复': {
        '问题现象': [
            '全量备份任务执行失败，错误码：GS-00512',
            '增量备份耗时异常，从1小时增加到6小时',
            '恢复测试失败，数据一致性校验不通过',
            '备份文件损坏，无法正常解压'
        ],
        '问题根因': [
            '备份存储空间不足，磁盘使用率达到98%',
            '备份期间有大事务运行，导致WAL日志堆积',
            '网络带宽被其他任务占用，传输速度下降',
            '备份脚本配置错误，参数设置不当'
        ],
        '分析过程': [
            [
                {'操作': '查看备份日志', '现象': '报错"No space left on device"', '现象分析': '磁盘空间不足'},
                {'操作': '检查磁盘使用情况', '现象': '/backup分区使用率98%', '现象分析': '需要清理或扩容'},
                {'操作': '分析历史备份', '现象': '过期备份未自动清理', '现象分析': '备份保留策略配置问题'}
            ],
            [
                {'操作': '检查备份任务状态', '现象': '任务卡在WAL归档阶段', '现象分析': 'WAL处理存在瓶颈'},
                {'操作': '查看活跃事务', '现象': '存在运行超过2小时的事务', '现象分析': '长事务影响备份'},
                {'操作': '监控IO性能', '现象': 'IO等待时间明显增加', '现象分析': 'IO竞争影响备份速度'},
                {'操作': '检查网络状况', '现象': '备份服务器网络丢包率5%', '现象分析': '网络问题导致传输慢'}
            ]
        ],
        '解决方案': [
            [
                {'描述': '清理过期备份', '具体命令': 'gs_probackup delete -B /backup --instance=prod --delete-expired'},
                {'描述': '扩展备份空间', '具体命令': 'lvextend -L +100G /dev/vg_data/lv_backup && resize2fs /dev/vg_data/lv_backup'}
            ],
            [
                {'描述': '终止长事务', '具体命令': 'SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state != \'idle\' AND query_start < now() - interval \'2 hours\';'},
                {'描述': '调整备份并行度', '具体命令': 'gs_probackup backup -B /backup --instance=prod -b FULL --threads=4'},
                {'描述': '配置备份保留策略', '具体命令': 'gs_probackup set-config -B /backup --instance=prod --retention-redundancy=7'}
            ]
        ]
    },
    '日志管理': {
        '问题现象': [
            '日志文件增长过快，每天产生50GB以上',
            '审计日志查询缓慢，无法满足合规审计要求',
            '错误日志中大量重复告警信息',
            '日志轮转失败，单个日志文件超过10GB'
        ],
        '问题根因': [
            '日志级别设置过低，记录了大量DEBUG信息',
            '审计策略配置不当，记录了不必要的操作',
            '日志轮转配置错误，cron任务未正确执行',
            '磁盘IO性能不足，日志写入成为瓶颈'
        ],
        '分析过程': [
            [
                {'操作': '查看日志配置', '现象': 'log_min_messages设置为DEBUG1', '现象分析': '日志级别过低'},
                {'操作': '分析日志内容', '现象': '90%为DEBUG级别日志', '现象分析': '大量无用日志'},
                {'操作': '检查磁盘增长', '现象': '日志目录每小时增长2GB', '现象分析': '需要调整日志策略'}
            ],
            [
                {'操作': '检查轮转配置', '现象': 'logrotate配置语法错误', '现象分析': '配置文件需要修正'},
                {'操作': '查看cron日志', '现象': 'logrotate任务执行失败', '现象分析': '定时任务异常'},
                {'操作': '验证权限设置', '现象': '日志目录权限为755', '现象分析': '权限配置正确'},
                {'操作': '手动执行轮转', '现象': '报错"file already exists"', '现象分析': '旧日志文件命名冲突'}
            ]
        ],
        '解决方案': [
            [
                {'描述': '调整日志级别', '具体命令': 'gs_guc reload -D /gaussdb/data -c "log_min_messages=WARNING"'},
                {'描述': '配置日志轮转', '具体命令': 'gs_guc reload -D /gaussdb/data -c "log_rotation_age=1d" -c "log_rotation_size=1GB"'}
            ],
            [
                {'描述': '修复logrotate配置', '具体命令': 'cat > /etc/logrotate.d/gaussdb << EOF\n/gaussdb/log/*.log {\n    daily\n    rotate 7\n    compress\n    missingok\n}\nEOF'},
                {'描述': '清理历史日志', '具体命令': 'find /gaussdb/log -name "*.log" -mtime +7 -delete'},
                {'描述': '验证配置生效', '具体命令': 'logrotate -d /etc/logrotate.d/gaussdb'}
            ]
        ]
    }
}

# 打分理由模板
score_reasons = {
    'high': [
        '问题描述清晰准确，根因分析深入，解决方案可复用性强',
        '分析过程逻辑严密，命令规范，文档质量高',
        '诊断步骤完整，每步都有明确的判断依据，值得推广'
    ],
    'medium': [
        '基本完成问题记录，但分析过程可以更详细',
        '解决方案有效但缺少验证步骤',
        '问题描述较清晰，根因分析不够深入'
    ],
    'low': [
        '问题描述过于简略，缺少关键信息',
        '分析过程不完整，跳过了必要的诊断步骤',
        '解决方案缺少具体命令，可操作性差'
    ]
}

# 生成10条记录
base_time = datetime(2024, 12, 1, 9, 0, 0)
records = []

for i in range(10):
    process_id = f'TICKET-{1001 + i}'
    issue_type = random.choice(issue_types)
    owner = random.choice(owners)

    template = templates[issue_type]

    create_time = base_time + timedelta(days=i*2, hours=random.randint(0, 8))
    update_time = create_time + timedelta(hours=random.randint(2, 48))

    problem = random.choice(template['问题现象'])
    root_cause = random.choice(template['问题根因'])
    analysis = json.dumps(random.choice(template['分析过程']), ensure_ascii=False)
    solution = json.dumps(random.choice(template['解决方案']), ensure_ascii=False)

    # 生成分数和理由
    score = round(random.uniform(5, 10), 1)
    diff_score = round(random.uniform(4, 10), 1)

    if score >= 8:
        reason = random.choice(score_reasons['high'])
    elif score >= 6:
        reason = random.choice(score_reasons['medium'])
    else:
        reason = random.choice(score_reasons['low'])

    records.append({
        'process_id': process_id,
        'issue_type': issue_type,
        'owner': owner,
        'create_time': create_time.strftime('%Y-%m-%d %H:%M:%S'),
        'update_time': update_time.strftime('%Y-%m-%d %H:%M:%S'),
        'problem': problem,
        'root_cause': root_cause,
        'analysis': analysis,
        'solution': solution,
        'diff_score': diff_score,
        'score': score,
        'reason': reason
    })

# 插入数据
for r in records:
    cursor.execute('''
        INSERT OR REPLACE INTO ticket_classification_2512 ("processId", "issueType", "owner")
        VALUES (?, ?, ?)
    ''', (r['process_id'], r['issue_type'], r['owner']))

    cursor.execute('''
        INSERT OR REPLACE INTO operations_kb
        ("流程ID", "create_time", "update_time", "问题现象", "问题根因", "分析过程", "解决方案", "diff_score", "得分", "理由")
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (r['process_id'], r['create_time'], r['update_time'], r['problem'],
          r['root_cause'], r['analysis'], r['solution'], r['diff_score'], r['score'], r['reason']))

conn.commit()

# 验证数据
print("=== 数据生成完成 ===\n")

cursor.execute('''
    SELECT T2."流程ID", C."issueType", C."owner", T2.create_time, T2.update_time,
           T2."问题现象", T2."问题根因", T2."分析过程", T2."解决方案", T2.diff_score, T2."得分", T2."理由"
    FROM operations_kb as T2, ticket_classification_2512 as C
    WHERE T2."流程ID" = C."processId"
    ORDER BY T2.update_time DESC, T2.create_time DESC
''')

rows = cursor.fetchall()
print(f"共查询到 {len(rows)} 条记录:\n")

for row in rows:
    print(f"{'='*60}")
    print(f"流程ID: {row[0]}")
    print(f"问题类型: {row[1]}")
    print(f"负责人: {row[2]}")
    print(f"创建时间: {row[3]}")
    print(f"更新时间: {row[4]}")
    print(f"问题现象: {row[5]}")
    print(f"问题根因: {row[6]}")
    print(f"分析过程: {row[7][:80]}...")
    print(f"解决方案: {row[8][:80]}...")
    print(f"diff_score: {row[9]}")
    print(f"得分: {row[10]}")
    print(f"理由: {row[11]}")
    print()

conn.close()
print(f"\n数据库文件已保存: gaussdb_ops.db")
