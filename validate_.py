import pandas as pd

ratio = pd.HDFStore("./ratio.h5")
print(ratio.keys())
res = ratio.get("USDJPY")

records = res.to_records()

print(res)

ratio.close()
