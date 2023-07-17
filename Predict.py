
import warnings
warnings.filterwarnings('ignore')
from mt5_command import linear_predict

symbol = 'XAUUSD'
## last day have closed = 0, not closed = 1 
day_not_closed = 1

# Predict today high&low
predict_high_d1 = linear_predict('linear_predict_high_model.pkl', symbol, day_not_closed)
predict_low_d1 = linear_predict('linear_predict_low_model.pkl', symbol, day_not_closed)

print("Next day predict!")
print('High: {:.4f}'.format(predict_high_d1))
print('Low: {:.4f}'.format(predict_low_d1))