# Import Libraries

# Import data
## Excel sheets
### test_data.xlsx
## Text Files
### main_prompt_task1.txt
### main_prompt_task2.txt
### system_prompt.txt

# Transform data
## test_data.xlsx
### Product Sheet = product_data dataframe
### General Details = general_data dataframe

# Invoke Agent
## Model = open ai chatgpt 4
## Internet access = TRUE

## System Prompt = system_prompt.txt

# Loop Through Data - for each row in product_data
## Prompt_1 =    Input English Language to be used: general_data[Langauge],
#               Brand Name: general_data[Brand],
#               Brand Story: general_data[Story],
#               Product Name: product_data[Product Name],
#               Product Category: product_data[Product Category],
#               Existing Product Description: product_data[Product Decription],
#               Images of the product: product_data[Images], - this is a list of URLs to images that the model needs to use to understand to create the output
#               SEO Key words input list: product_data[SEO Details],
#               Made in Country: product_data[Made In],
#                + main_prompt_task1.txt
## Prompt_2 =    Input English Language to be used: general_data[Langauge],
#               Brand Name: general_data[Brand],
#               Brand Story: general_data[Story],
#               Product Name: product_data[Product Name],
#               Product Category: product_data[Product Category],
#               Existing Product Description: product_data[Product Decription],
#               Images of the product: product_data[Images], - this is a list of URLs to images that the model needs to use to understand to create the output
#               SEO Key words input list: product_data[SEO Details],
#               Made in Country: product_data[Made In],
#                + main_prompt_task2.txt
## Save response for each
## product_data_response dataframe
### Product Token = product_data[Product Token]
#### Product Title = Response to Prompt 1
#### Product Desription = Response to Prompt 2

# Write Data to file
## Save product_data_response dataframe as .xlsx

# Finish