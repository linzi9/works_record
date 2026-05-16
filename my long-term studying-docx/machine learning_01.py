class Linearmodel: #定义类
    def __init__(self): #定义类的构造方法
        self.omega=0;#定义类的属性
        self.b=0
    def fit(self,x_truth,y_truth):#定义了训练模型的方法
        self.omega=(y_truth[0]-y_truth[1])/(x_truth[0]-x_truth[1]);
        self.b=y_truth[0]-self.omega*x_truth[0]
        return
    def predict(self,x_test):#定义了使用模型进行预测的方法
        y_test=self.omega*x_test+self.b
        return y_test

    
        
