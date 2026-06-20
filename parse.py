import json
import extract


def extract_latest(json_data, keys):
    best_data = []
    max_year = 0

    for key in keys:
        try:
            arr = json_data["facts"]["us-gaap"][key]["units"]["USD"]
        except (KeyError, TypeError):
            continue
        if not isinstance(arr, list):
            continue

        current_data = []
        for item in arr:
            if item.get("form") != "10-K":
                continue
            date = item.get("end") or ""
            val = item.get("val") or 0
            if len(date) < 4:
                continue
            current_data.append((date, val))

        if not current_data:
            continue

        current_data.sort(key=lambda x: x[0], reverse=True)

        deduped = []
        for date, val in current_data:
            if deduped and deduped[-1][0][:4] == date[:4]:
                continue
            deduped.append((date, val))
        current_data = deduped

        latest_date, _ = current_data[0]
        try:
            year = int(latest_date[:4])
        except ValueError:
            continue
        if year > max_year:
            max_year = year
            best_data = current_data

    return best_data[:5]


class Data:
    def __init__(
        self,
        netincomeloss=None,
        assets=None,
        stockholdersequity=None,
        revenues=None,
        operatingincomeloss=None,
        liabilities=None,
    ):
        self.netincomeloss = netincomeloss or []              # 순이익
        self.assets = assets or []                            # 총자산
        self.stockholdersequity = stockholdersequity or []    # 자기자본
        self.revenues = revenues or []                        # 매출
        self.operatingincomeloss = operatingincomeloss or []  # 영업이익
        self.liabilities = liabilities or []                  # 부채

    @staticmethod
    def new(ticker: str) -> "Data":
        path = extract.facts_file_path(ticker)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        json_data = json.loads(content)

        netincomeloss = extract_latest(
            json_data,
            ["NetIncomeLoss", "NetIncomeLossAvailableToCommonStockholdersBasic"],
        )
        assets = extract_latest(json_data, ["Assets"])
        liabilities = extract_latest(json_data, ["Liabilities", "LiabilitiesCurrent"])
        stockholdersequity = extract_latest(
            json_data,
            [
                "StockholdersEquity",
                "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            ],
        )

        if not stockholdersequity and assets and liabilities:
            calculated_equity = []
            for date, ast_val in assets:
                ast_yr = date[:4]
                liab_val = next(
                    (lv for ld, lv in liabilities if len(ld) >= 4 and ld[:4] == ast_yr),
                    None,
                )
                if liab_val is not None:
                    calculated_equity.append((date, ast_val - liab_val))
            stockholdersequity = calculated_equity

        revenues = extract_latest(
            json_data,
            [
                "Revenues",
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "SalesRevenueNet",
            ],
        )
        operatingincomeloss = extract_latest(json_data, ["OperatingIncomeLoss", "OperatingLoss"])

        return Data(
            netincomeloss=netincomeloss,
            assets=assets,
            stockholdersequity=stockholdersequity,
            revenues=revenues,
            operatingincomeloss=operatingincomeloss,
            liabilities=liabilities,
        )
