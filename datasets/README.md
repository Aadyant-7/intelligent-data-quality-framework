# Public demo data

The hosted site is read-only. These CSV files are copied into its temporary upload directory when the API starts; the local upload library is separate.

| File | Rows | Source | Use |
| --- | ---: | --- | --- |
| `online_retail_sample.csv` | 5,000 | [UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail), first 5,000 rows of the reference workbook | UK invoice, stock code, and description checks |
| `retail_store_sales_demo.csv` | 12,575 | Full Ahmed Mohamed [Retail Store Sales: Dirty for Data Cleaning](https://www.kaggle.com/datasets/ahmedmohamed2003/retail-store-sales-dirty-for-data-cleaning) CSV, supplied for local testing | Alternate headers, missingness, and price × quantity checks |
| `supermarket_sales_demo.csv` | 1,000 | [Supermarket Sales Analysis data](https://github.com/vikramnayyar/Supermarket-Sales-Analysis/tree/main/data), originally from [Kaggle Supermarket Sales](https://www.kaggle.com/datasets/aungpyaeap/supermarket-sales) | Tax-inclusive total checks |

The dirty retail CSV is attributed to Ahmed Mohamed and follows the source dataset's CC BY-SA 4.0 terms. It remains available under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). The supermarket CSV comes from the linked Apache-2.0 repository; its README attributes the underlying dataset to Kaggle. These examples are for education, not proof that a dataset is fit for a particular use. The source files are not user uploads.
