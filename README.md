# 1. Top 10 Protocol Selection

The experiment uses 10 major Ethereum ecosystem protocols:

1. Aave
2. Balancer
3. Compound
4. Curve
5. ENS
6. EigenLayer
7. Lido
8. Morpho
9. Pendle
10. Uniswap

For each protocol, official Ethereum Mainnet production/core contract addresses were collected from official documentation or official project repositories.

**Seed Dataset:**
```
data/input/top_10_addresses.csv
```

## Layer 1 Discovery

### Data Source
Layer 1 address discovery uses the Alchemy Ethereum Mainnet Transfers API.
by:
```
alchemy_getAssetTransfers
```

## Pagination
Alchemy's Transfers API can return multiple pages of results.

Script supports pagination using.
`pageKey` of Alchemy's

**intentionally something like:**
```
Request page ---> Receive transfers ---> pageKey ?
                                            |
                                            |--- No -> Finished
                                            |
                                            |--- Yes
                                                  |
                                            Request next page
```

But for the current demonstration, the traversal is intentionally limited to:
```
2 pages per direction per seed contract
```

The purpose of this limit is to demonstrate the methodology, measure graph growth, and avoid performing a large historical extraction before deciding whether deeper traversal is worthwhile.

## Output
```
data/output/top_10_related_addresses.csv
```
```
data/output/layer1_growth_summary.csv
```

## Growth by Protocol:

| Protocol | Seed Contracts | Relationship Edges | Unique Related Addresses |
|----------|----------------|--------------------|--------------------------|
| Aave     | 2              | 63                 | 45                       |
| Balancer | 1              | 400                | 32                       |
| Compound | 2              | 639                | 208                      |
| Curve    | 1              | 10                 | 3                        |
| ENS      | 2              | 298                | 63                       |
| EigenLayer | 4            | 1,055              | 537                      |
| Lido     | 2              | 402                | 303                      |
| Morpho   | 1              | 400                | 44                       |
| Pendle   | 1              | 374                | 139                      |
| Uniswap  | 4              | 859                | 215                      |
| Total    | 27             | 4,500              | 1,572                    |

## Project Structure
```
ethereum-top10-analysis/
|
|--- .venv/
|--- data/
|    |--- input/
|    |    |--- top_10_addresses.csv
|    |
|    |--- output/
|         |--- layer1_growth_summary.csv
|         |--- top_10_related_addresses.csv
|
|
|--- src/
|    |--- layer1_discovery.py
|
|--- .env
|--- .gitignore
|--- README.md
|--- README.pdf
|--- requirements.txt
```