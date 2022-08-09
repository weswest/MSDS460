# Assignment

Wes note: I'm not going to copy the entire assignment here (see code for details of inputs).  Top level, there is a set of currency exchanges across five currencies, structured so that if you exchange USD-->EUR-->USD you end up with less money than you started.

Key question is how to formulate the cheapest trading plan, ensuring a certain goal amount of two currencies while maintaining a minimum amount of the other currencies.

The writeup then asks the following questions:
1. Create a model for this problem and solve it.
2. What is the optimal trading plan?
3. What is the optimal transaction cost (in equivalent USD)?
4. Suppose another executive thinks that holding $250,000 USD in each currency is excessive and wants to lower the amount to $50,000 USD in each currency. Does this help to lower the transaction cost? Why or why not?
5. Suppose the exchange rate for converting USD to GBP increased from 0.6409 to 0.6414. What happens to the optimal solution in this case?

# My Writeup

See the pdf file for the writeup.  Not pasted here since it has a bunch of LaTeX equations and I didn't want to mess around with inserting them into this readme

# What's Next

One of the things I was challenging myself to accomplish with this was to address the problem programmatically rather than explicitly.  So I was really trying to, e.g., use dictionaries for variables.  Two items that I'm not thrilled with:

1. My creation of intermediate variables (e.g., end_USD) should have similarly been stored in a dictionary rather than made explicit
2. I couldn't figure out how to execute the model as a function without creating a ton of inputs.  So rather minor changes to the input assumptions required a full rescoping of the model.

But hey, the joy of doing this as schoolwork is that you have to deliver by the delivery date.  It worked as-is well enough, so I move forward.
