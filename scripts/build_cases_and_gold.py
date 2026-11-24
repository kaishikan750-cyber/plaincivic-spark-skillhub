"""Generate the 10-case pre-committed benchmark dataset and gold labels for PlainCivic.

Run and commit BEFORE local Spark-X2.6-4B inference so evaluation criteria are locked in advance.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(r"C:\Users\qqq\.gemini\antigravity\scratch\plaincivic-spark-skillhub")
CASES_DIR = ROOT / "cases"
GOLD_DIR = ROOT / "gold"

REFERENCE_DATE = "2026-11-24"

CASES = [
    {
        "case_id": "C01",
        "slug": "nia-work-residence-permit",
        "title_zh": "外国人工作类居留许可首次申办（2年期）",
        "title_en": "Foreign National Work Residence Permit (First-Time, 2-Year Validity)",
        "mode": "bilingual",
        "target_user": "Newly arrived non-Chinese-speaking software engineer in China preparing an in-person PSB Exit-Entry Administration counter visit",
        "reference_date": REFERENCE_DATE,
        "service": "外国人工作类居留许可办理",
        "profile_summary": "外籍在职工程师，单人首次申办（无随迁家属），2026-11-01持Z签证入境，拟申请2年期工作类居留许可，现场本人办理。",
        "sources": [
            {
                "id": "S1",
                "filename": "nia_work_residence_permit_guide.txt",
                "source_type": "public_official_guide_excerpt",
                "source_url": "https://www.nia.gov.cn/",
                "source_date": "2026-11-24",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】外国人工作类居留证件签发（首次申办）",
                    "L2: 【申请时限】持签证入境后需办理居留证件的，应当自入境之日起30日内向拟居留地公安机关出入境管理机构提出申请。",
                    "L3: 【基本材料1】本人有效护照或者其他国际旅行证件原件。",
                    "L4: 【基本材料2】填写完整并签署的《外国人签证证件申请表》，提交一张符合《出入境证件相片照相指引》标准的近期白底彩色免冠照片。",
                    "L5: 【基本材料3】外国人来华工作许可证明及聘用单位出具的工作单位证明函件原件。",
                    "L6: 【条件材料1】申请有效期1年以上居留证件的，须提交当地卫生检疫部门或指定医疗机构出具的6个月内有效《身体健康证明》原件。",
                    "L7: 【条件材料2】有随迁家属一同申请的，须提交经认证的亲属关系证明原件及复印件。",
                    "L8: 【办理时限】公安机关出入境管理机构作出的受理回执有效期自受理之日起不超过15个工作日。",
                    "L9: 【办理方式】首次申请居留证件须由申请人本人到场办理并留存生物特征，不可委托他人代办。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "本人有效护照原件", "details": "有效期至2029-08-20，含2026-11-01入境章（Z字签证）"},
            {"id": "I02", "name": "外国人签证证件申请表", "details": "已打印填写并由本人签字"},
            {"id": "I03", "name": "证件照片", "details": "近期蓝底彩色免冠照片2张（非白底）"},
            {"id": "I04", "name": "外国人工作许可证及单位在职证明函", "details": "均为盖章原件，日期2026-11-18"},
            {"id": "I05", "name": "体检报告", "details": "海外诊所2026-03-10出具的英文体检报告复印件（距2026-11-24已超过8个月，且非当地卫生检疫部门或指定医疗机构原件）"}
        ]
    },
    {
        "case_id": "C02",
        "slug": "nia-visa-extension",
        "title_zh": "外国人L字旅游签证停留期限延期",
        "title_en": "Foreign Visitor L-Visa Stay Duration Extension",
        "mode": "bilingual",
        "target_user": "Foreign tourist whose L-visa expires in 5 days trying to extend stay without missing the statutory advance deadline",
        "reference_date": REFERENCE_DATE,
        "service": "外国人L字签证停留期限延期",
        "profile_summary": "外籍个人游客，持L字签证，当前停留期限至2026-11-29（距参考日2026-11-24仅剩5天），本人到场申请延期。",
        "sources": [
            {
                "id": "S1",
                "filename": "nia_visa_extension_guide.txt",
                "source_type": "public_official_guide_excerpt",
                "source_url": "https://www.nia.gov.cn/",
                "source_date": "2026-11-24",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】外国人申请延长签证停留期限（L字旅游签证）",
                    "L2: 【申请时限】外国人申请延长签证停留期限，应当在签证注明的停留期限届满7日前向当地公安机关出入境管理机构提出申请。",
                    "L3: 【基本材料1】本人有效护照或者其他国际旅行证件原件。",
                    "L4: 【基本材料2】填写完整并签署的《外国人签证证件申请表》及近期白底彩色免冠照片1张。",
                    "L5: 【基本材料3】与申请事由相关的行程计划安排说明（含后续住宿预订或离境机票预订单）；团体旅游还须提交旅行社证明函件。",
                    "L6: 【办理时限】受理回执有效期自受理之日起不超过7个工作日。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "本人有效护照原件", "details": "L字签证停留期限至2026-11-29"},
            {"id": "I02", "name": "外国人签证证件申请表与白底彩照", "details": "已签字，附近期白底免冠彩照1张"}
        ]
    },
    {
        "case_id": "C03",
        "slug": "passport-renewal-elderly",
        "title_zh": "老年人普通护照到期换发（清晰就绪案例）",
        "title_en": "Senior Citizen Ordinary Passport Renewal (Ready Case)",
        "mode": "plain_zh",
        "target_user": "68-year-old retired citizen checking whether all documents are complete before visiting the exit-entry hall",
        "reference_date": REFERENCE_DATE,
        "service": "中国公民普通护照换发",
        "profile_summary": "68岁退休居民（原民营企业员工，非登记备案国家工作人员），本人现场办理普通护照换发，现持护照将于2027-03-10到期（剩余不足4个月）。",
        "sources": [
            {
                "id": "S1",
                "filename": "nia_ordinary_passport_renewal.txt",
                "source_type": "public_official_guide_excerpt",
                "source_url": "https://www.nia.gov.cn/",
                "source_date": "2026-11-24",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】中国公民普通护照换发",
                    "L2: 【办理条件】护照有效期不足6个月，或签证页即将使用完毕，可申请换发普通护照。",
                    "L3: 【基本材料1】有效期内的原普通护照原件。",
                    "L4: 【基本材料2】本人有效居民身份证原件。",
                    "L5: 【基本材料3】填写完整的《中国公民出入境证件申请表》及符合标准的出入境证件相片（含回执）。",
                    "L6: 【条件材料1】未满16周岁的未成年人，须提交户口簿及监护人身份证原件并由监护人陪同。",
                    "L7: 【条件材料2】登记备案的国家工作人员，须按干部管理权限提交单位出具的同意出境意见函。",
                    "L8: 【办理时限】公安机关出入境管理机构自受理之日起7至15个工作日内办结。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "原普通护照原件", "details": "有效期至2027-03-10（距2026-11-24约3.5个月，不足6个月）"},
            {"id": "I02", "name": "居民身份证原件", "details": "长期有效"},
            {"id": "I03", "name": "申请表与出入境相片回执", "details": "已完成现场照相取得合格回执并填写申请表"}
        ]
    },
    {
        "case_id": "C04",
        "slug": "cross-province-medical-filing",
        "title_zh": "老年人跨省异地就医备案（身份条件缺失待确认）",
        "title_en": "Elderly Cross-Province Medical Insurance Filing (Unknown Applicability Trap)",
        "mode": "plain_zh",
        "target_user": "71-year-old retiree moving across provinces to stay with family; profile does not specify whether filing as long-term resident or hospital referral",
        "reference_date": REFERENCE_DATE,
        "service": "跨省异地就医直接结算备案",
        "profile_summary": "71岁城镇职工医保退休人员，计划前往外省子女处居住并看病，但未说明是否已取得当地居住证/户籍、是否采用个人承诺制，也未说明是否属于医院转诊。",
        "sources": [
            {
                "id": "S1",
                "filename": "cross_province_medical_filing.txt",
                "source_type": "public_official_guide_excerpt",
                "source_url": "https://www.gz.gov.cn/",
                "source_date": "2026-11-24",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】跨省异地就医直接结算备案",
                    "L2: 【基本材料1】有效身份证件或社会保障卡（或医保电子凭证）。",
                    "L3: 【基本材料2】填写完整的《跨省异地就医备案表》。",
                    "L4: 【条件材料1】异地长期居住人员须提交异地户籍证明、居住证、单位派驻证明或个人承诺书之一。",
                    "L5: 【条件材料2】异地转诊就医人员须提交具有转诊资质的定点医疗机构开具的《转诊转院证明》。",
                    "L6: 【办理时限】线上通过国家医保服务平台App办理一般1个工作日内办结；线下窗口材料齐全当场办结。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "居民身份证与社会保障卡原件", "details": "均在有效期内"},
            {"id": "I02", "name": "跨省异地就医备案表", "details": "已填写基本信息"}
        ]
    },
    {
        "case_id": "C05",
        "slug": "residence-permit-application",
        "title_zh": "城市居住证初次申领（居住登记不满半年 + 仅手机照片）",
        "title_en": "Urban Residence Permit Application (6-Month Eligibility & Phone Photo Trap)",
        "mode": "plain_zh",
        "target_user": "Migrant worker checking if they can apply for a local residence permit after 3 months with a phone photo of their lease",
        "reference_date": REFERENCE_DATE,
        "service": "居住证申领",
        "profile_summary": "外地来沪务工人员，2026-08-15办理居住登记（距2026-11-24仅约3个月零9天），在当地租房，拟本人现场申领居住证。",
        "sources": [
            {
                "id": "S1",
                "filename": "mps_residence_permit_regulation.txt",
                "source_type": "public_official_guide_excerpt",
                "source_url": "https://www.mps.gov.cn/",
                "source_date": "2026-11-24",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】居住证申领（依据《居住证暂行条例》）",
                    "L2: 【前置条件】公民离开常住户口所在地，到其他城市居住并办理居住登记满半年以上，符合合法稳定就业、合法稳定住所或连续就读条件之一的，可以申领居住证。",
                    "L3: 【基本材料1】本人居民身份证原件。",
                    "L4: 【基本材料2】申领人近期标准证件相片。",
                    "L5: 【基本材料3】合法稳定住所证明（房屋租赁合同或房屋产权证明原件及复印件1份），或劳动合同/在读证明原件及复印件1份。",
                    "L6: 【办理时限】符合条件的，自受理之日起15日内制作发放居住证；交通不便地区最长不超过30日。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "居住登记凭证", "details": "登记日期为2026-08-15"},
            {"id": "I02", "name": "本人居民身份证原件", "details": "有效期内"},
            {"id": "I03", "name": "近期标准证件相片", "details": "纸质2张"},
            {"id": "I04", "name": "租房合同照片", "details": "仅有手机拍摄的租赁合同照片，无纸质原件及复印件"}
        ]
    },
    {
        "case_id": "C06",
        "slug": "housing-fund-rent-withdrawal",
        "title_zh": "住房公积金无房租房提取（未婚排除结婚证，全部就绪）",
        "title_en": "Housing Provident Fund Rent Withdrawal (Unmarried Exclusion, Ready Case)",
        "mode": "plain_zh",
        "target_user": "Young single renter checking whether a marriage certificate is needed for rent withdrawal",
        "reference_date": REFERENCE_DATE,
        "service": "住房公积金租房提取",
        "profile_summary": "未婚单身职工，已连续足额缴存住房公积金8个月，在缴存城市名下无自有住房，本人携带证件办理。",
        "sources": [
            {
                "id": "S1",
                "filename": "synthetic_housing_fund_rent_guide.txt",
                "source_type": "synthetic_civic_notice",
                "source_date": "2026-10-15",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】住房公积金无房租房提取（示范模拟政务指南）",
                    "L2: 【办理条件】申请人须在本市连续足额缴存住房公积金满3个月，且本人及配偶在本市无自有住房。",
                    "L3: 【基本材料1】申请人有效居民身份证原件。",
                    "L4: 【基本材料2】申请人本人名下I类银行借记卡原件。",
                    "L5: 【条件材料1】已婚申请人须提供结婚证原件及配偶身份证复印件。",
                    "L6: 【办理时限】审核通过后3个工作日内资金划转至指定银行卡；免收手续费。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "公积金缴存与无房记录", "details": "连续足额缴存8个月，本市无自有住房"},
            {"id": "I02", "name": "居民身份证原件", "details": "有效期内"},
            {"id": "I03", "name": "本人I类银行借记卡原件", "details": "状态正常"}
        ]
    },
    {
        "case_id": "C07",
        "slug": "multi-source-conflict-senior-card",
        "title_zh": "老年人免费乘车敬老卡办理（新旧两份通知直接冲突）",
        "title_en": "Senior Free Transit Card (Conflicting Community Poster vs District Notice)",
        "mode": "plain_zh",
        "target_user": "62-year-old resident confused between an old community bulletin board poster and a newer district notice",
        "reference_date": REFERENCE_DATE,
        "service": "老年人敬老卡（免费乘车卡）申领",
        "profile_summary": "62周岁本市户籍居民，本人持身份证和手机电子证件照前往办理，手上同时拿到了小区旧公告(S1)和区里新通知(S2)。",
        "sources": [
            {
                "id": "S1",
                "filename": "community_poster_2024.txt",
                "source_type": "synthetic_civic_notice",
                "source_date": "2024-05-01",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【小区宣传栏通知】老年人敬老卡办理须知（2024年5月张贴）",
                    "L2: 办理年龄：仅限年满65周岁及以上的本市户籍老年人办理。",
                    "L3: 必备材料：身份证原件、户口簿原件、近期2寸纸质彩色照片2张。",
                    "L4: 办理费用：首次办卡收取工本费20元。"
                ]
            },
            {
                "id": "S2",
                "filename": "district_notice_2026.txt",
                "source_type": "synthetic_civic_notice",
                "source_date": "2026-09-15",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【区民政与交通局联合通知】2026年敬老卡便民升级通知（2026年9月15日发布）",
                    "L2: 办理年龄：年满60周岁及以上的常住老年人即可申领。",
                    "L3: 必备材料：身份证原件即可，现场免费采集电子照片，无需携带纸质照片及户口簿。",
                    "L4: 办理费用：首次申领免收工本费。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "居民身份证原件", "details": "年龄62周岁，本市户籍"},
            {"id": "I02", "name": "手机电子证件照", "details": "无2寸纸质照片，未带户口簿"}
        ]
    },
    {
        "case_id": "C08",
        "slug": "no-deadline-stated-library-card",
        "title_zh": "社区无障碍盲文/有声图书借阅证办理（无截止期+免收费防幻觉）",
        "title_en": "Accessible Braille & Audio Library Card (No Deadline Stated & Zero Fee Trap)",
        "mode": "plain_zh",
        "target_user": "Visually impaired resident applying for free accessible braille/audio home-delivery library membership",
        "reference_date": REFERENCE_DATE,
        "service": "公共图书馆无障碍借阅证办理",
        "profile_summary": "视障读者，本人持身份证及残疾人证申请免费上门寄送盲文与有声读物服务，希望确认是否收费以及有没有截止日期。",
        "sources": [
            {
                "id": "S1",
                "filename": "synthetic_accessible_library_guide.txt",
                "source_type": "synthetic_civic_notice",
                "source_date": "2026-10-01",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】市公共图书馆无障碍阅读服务读者证办理（示范模拟指南）",
                    "L2: 【费用说明】免收押金与工本费，盲文及有声读物免费邮寄上门。",
                    "L3: 【基本材料】本人有效居民身份证原件（或社保卡原件）。",
                    "L4: 【条件材料】申请“免费上门寄送盲文/有声读物”专项服务的读者，须出示《中华人民共和国残疾人证》原件（或电子残疾人证）。",
                    "L5: 【服务时间】全年常态化开放办理（周二至周日 09:00-17:00，周一闭馆），不设报名截止日期。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "居民身份证原件", "details": "有效期内"},
            {"id": "I02", "name": "电子残疾人证", "details": "有效期内，视力残疾类别"}
        ]
    },
    {
        "case_id": "C09",
        "slug": "child-school-enrollment-proxy",
        "title_zh": "社区暑托/青少年公益班祖辈代办报名（过期体检+缺复印件+缺委托书）",
        "title_en": "Grandparent Proxy Enrollment for Community Youth Program (Expiry + Copies + Proxy Trap)",
        "mode": "plain_zh",
        "target_user": "Grandfather handling offline registration on behalf of parents for an 8-year-old grandchild",
        "reference_date": REFERENCE_DATE,
        "service": "社区青少年公益托管班线下报名",
        "profile_summary": "孩子的爷爷（非法定监护人）代父母现场为8岁孙子办理报名，参考日期2026-11-24。",
        "sources": [
            {
                "id": "S1",
                "filename": "synthetic_youth_program_notice.txt",
                "source_type": "synthetic_civic_notice",
                "source_date": "2026-11-10",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】社区寒假青少年公益托管班线下报名须知（示范模拟通知）",
                    "L2: 【报名截止】2026年11月28日16:00前至街道服务中心3号窗口提交，逾期不予受理。",
                    "L3: 【基本材料1】儿童户口簿原件及复印件2份。",
                    "L4: 【基本材料2】社区医院出具的30日内有效儿童健康体检单原件。",
                    "L5: 【条件材料1】非监护人本人代办的，须提交监护人亲笔签字的《授权委托书》原件及代办人身份证原件。"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "儿童户口簿原件及复印件", "details": "原件1本，但仅复印了1份（少1份）"},
            {"id": "I02", "name": "儿童健康体检单原件", "details": "开具日期2026-10-01（距2026-11-24已54天，超过30日有效期）"},
            {"id": "I03", "name": "代办人（爷爷）身份证原件", "details": "有效期内，但未带父母签字的授权委托书"}
        ]
    },
    {
        "case_id": "C10",
        "slug": "bilingual-university-scholarship-subsidy",
        "title_zh": "高校毕业生租房补贴双语申报（硬截止时间 + 附件模糊不可读门禁）",
        "title_en": "Graduate Rental Subsidy Bilingual Notice (Hard Deadline + Unreadable Annex Gate)",
        "mode": "bilingual",
        "target_user": "International graduate applying for a municipal rental subsidy before a hard deadline where Annex B table scan is illegible",
        "reference_date": REFERENCE_DATE,
        "service": "高校毕业生租房补贴申报",
        "profile_summary": "2026届外籍硕士毕业生，已在本市签订2年劳动合同并缴纳社保2个月，持有学位认证与备案租房合同，拟于2026-11-25提交申报。",
        "sources": [
            {
                "id": "S1",
                "filename": "synthetic_graduate_subsidy_bilingual.txt",
                "source_type": "synthetic_civic_notice",
                "source_date": "2026-11-01",
                "currentness": "user_provided_current",
                "lines": [
                    "L1: 【事项名称】2026年度高校毕业生租房补贴申报公告（示范模拟公告）",
                    "L2: 【申报截止】2026年11月1日至2026年11月30日17:00，逾期系统自动关闭、不予补报。",
                    "L3: 【资格条件】毕业2年内的全日制本科及以上毕业生，在本市用人单位签订1年以上劳动合同并正常缴纳社会保险。",
                    "L4: 【基本材料1】毕业证及学位证（境外学历须附教育部留学服务中心认证书）扫描件。",
                    "L5: 【基本材料2】有效期内劳动合同及社保缴费明细。",
                    "L6: 【基本材料3】经住建部门备案的房屋租赁合同。",
                    "L7: 【附件说明】[附件B：分学历与分区域补贴金额分级标准及特殊扣减条款——原图扫描严重模糊，文字与数字无法识别]"
                ]
            }
        ],
        "inventory": [
            {"id": "I01", "name": "硕士学位证及留服认证书扫描件", "details": "2026年6月毕业，认证有效"},
            {"id": "I02", "name": "2年期劳动合同及社保缴费明细", "details": "正常在缴2个月"},
            {"id": "I03", "name": "住建部门备案房屋租赁合同", "details": "有效期内"}
        ]
    }
]

GOLD = {
    "schema_version": "1.0",
    "reference_date": REFERENCE_DATE,
    "cases": {
        "C01": {
            "expected_overall_status": "not_ready",
            "traps": ["T1_expiry_date_math", "T2_format_original_vs_photo", "T4_not_applicable_no_false_block"],
            "must_have_statuses": {"expired_or_conflict": ["身体健康证明", "体检"], "conflict_or_missing": ["白底", "照片"], "not_applicable": ["亲属关系", "随迁家属"]},
            "survival_clauses": {
                "eligibility": ["1年以上", "本人到场"],
                "documents": ["护照", "白底", "工作许可", "6个月内"],
                "deadlines": ["30日内", "15个工作日"]
            },
            "bilingual_survival_en": ["30 days", "15 working days", "white", "1 year", "6 months", "in person"]
        },
        "C02": {
            "expected_overall_status": "not_ready",
            "traps": ["T1_expiry_date_math"],
            "must_have_statuses": {"missing": ["行程", "机票", "住宿"], "expired_or_conflict": ["7日前"]},
            "survival_clauses": {
                "eligibility": ["L字"],
                "documents": ["护照", "申请表", "行程"],
                "deadlines": ["7日前", "7个工作日"]
            },
            "bilingual_survival_en": ["7 days", "7 working days", "passport", "itinerary"]
        },
        "C03": {
            "expected_overall_status": "ready",
            "traps": ["T4_not_applicable_no_false_block"],
            "must_have_statuses": {"not_applicable": ["未满16周岁", "国家工作人员"]},
            "survival_clauses": {
                "eligibility": ["不足6个月"],
                "documents": ["原普通护照", "居民身份证", "相片"],
                "deadlines": ["7至15个工作日"]
            },
            "bilingual_survival_en": []
        },
        "C04": {
            "expected_overall_status": "needs_confirmation",
            "traps": ["T3_unknown_identity_no_guess"],
            "must_have_statuses": {"needs_confirmation": ["居住证", "承诺书", "转诊"]},
            "survival_clauses": {
                "eligibility": ["异地长期居住", "异地转诊"],
                "documents": ["身份证", "备案表"],
                "deadlines": ["1个工作日", "当场办结"]
            },
            "bilingual_survival_en": []
        },
        "C05": {
            "expected_overall_status": "not_ready",
            "traps": ["T1_expiry_date_math", "T2_format_original_vs_photo"],
            "must_have_statuses": {"missing_or_conflict": ["租赁合同", "原件"], "conflict_or_missing_elig": ["满半年"]},
            "survival_clauses": {
                "eligibility": ["满半年"],
                "documents": ["身份证原件", "复印件1份"],
                "deadlines": ["15日内", "30日"]
            },
            "bilingual_survival_en": []
        },
        "C06": {
            "expected_overall_status": "ready",
            "traps": ["T4_not_applicable_no_false_block"],
            "must_have_statuses": {"not_applicable": ["结婚证"]},
            "survival_clauses": {
                "eligibility": ["满3个月", "无自有住房"],
                "documents": ["身份证原件", "I类银行借记卡"],
                "deadlines": ["3个工作日"]
            },
            "bilingual_survival_en": []
        },
        "C07": {
            "expected_overall_status": "not_ready",
            "traps": ["T5_multi_source_conflict"],
            "must_have_statuses": {"conflict": ["65周岁", "60周岁", "纸质", "电子", "20元", "免收"]},
            "survival_clauses": {
                "eligibility": ["65周岁", "60周岁"],
                "documents": ["身份证原件", "纸质", "电子"],
                "deadlines": ["2024", "2026"]
            },
            "bilingual_survival_en": []
        },
        "C08": {
            "expected_overall_status": "ready",
            "traps": ["T6_no_invented_deadline_or_fee"],
            "must_have_statuses": {"ready": ["身份证", "残疾人证"]},
            "survival_clauses": {
                "eligibility": ["免收押金与工本费"],
                "documents": ["身份证", "残疾人证"],
                "deadlines": ["不设报名截止日期", "09:00-17:00"]
            },
            "bilingual_survival_en": []
        },
        "C09": {
            "expected_overall_status": "not_ready",
            "traps": ["T1_expiry_date_math", "T2_format_original_vs_photo"],
            "must_have_statuses": {"expired": ["体检单", "30日"], "missing_or_conflict": ["复印件2份", "授权委托书"]},
            "survival_clauses": {
                "eligibility": ["非监护人本人代办"],
                "documents": ["复印件2份", "30日内", "授权委托书"],
                "deadlines": ["2026年11月28日16:00"]
            },
            "bilingual_survival_en": []
        },
        "C10": {
            "expected_overall_status": "needs_confirmation",
            "traps": ["T7_unreadable_section_gate"],
            "must_have_statuses": {"needs_confirmation": ["附件B", "模糊"]},
            "survival_clauses": {
                "eligibility": ["毕业2年内", "1年以上劳动合同"],
                "documents": ["认证书", "社保", "备案"],
                "deadlines": ["2026年11月30日17:00"]
            },
            "bilingual_survival_en": ["2026", "17:00", "2 years", "1 year", "unreadable"]
        }
    }
}


def main() -> None:
    CASES_DIR.mkdir(parents=True, exist_ok=True)
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        p = CASES_DIR / f"{case['case_id']}_{case['slug']}.json"
        p.write_text(json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {p.name}")
    gp = GOLD_DIR / "gold.json"
    gp.write_text(json.dumps(GOLD, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {gp}")


if __name__ == "__main__":
    main()
