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
    
def main():#定义一个函数main,相当于是程序的主函数
    s=input("input X1,Y1,X2,Y2:");#从键盘输入4个数据
    s=eval(s).replace(","," ")
    sList=s.split();#把字符串（这4个数据）拆成4个字符串，并输出成列表

    if len(sList) != 4:
        print("错误!请输入4个数字,用逗号或空格分隔！")
        return
    
    x=[]; y=[];
    x.append(eval(sList[0]));y.append(eval(sList[1])); #这里的eval函数是用来把字符串转数字的
    x.append(eval(sList[2]));y.append(eval(sList[3]));
    
    lm=Linearmodel();
    lm.fit(x,y)
    print("training result: omega=", lm.omega ,",b=",lm.b, "\n")

    x = eval(input("input:x"))
    y=lm.predict(x)
    print("predict result : x=",x,"平方米时，" , "y=",y,"万元")
    return

main()

    
        
