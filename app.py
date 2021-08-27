from flask import Flask, render_template,request, url_for,redirect,flash,session,jsonify
from flask_mysqldb import MySQL
from flask_bcrypt import bcrypt
import yaml
import re
app = Flask(__name__)
app.secret_key = "dbms"
  
db=yaml.load(open('db.yaml'))

app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)




@app.route("/")
def index():

    return render_template('login.html')

@app.route('/logout', methods=["GET", "POST"])
def logout():
      session.clear()
      return render_template("login.html")

@app.route("/",methods=['GET','POST'])
def authenticiate():
    msg = ''
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cur.execute("SELECT * FROM emp WHERE emp_username=%s AND emp_password=%s",(username,password))
        data=cur.fetchall()
        cur.close()
        if len(data)>0:
           
           return redirect(url_for('status'))
        else:
            flash("wrong username/password")
            return render_template('login.html')
    return render_template('login.html')

# SUPPLIER START  

@app.route("/supplier")
def supplier():
    cur = mysql.connection.cursor()
    cur.execute("SELECT Supplier.S_ID, Supplier.S_name,Supplier.S_mail,Supplier.firm_no,Supplier.street_name,GROUP_CONCAT(DISTINCT Supplier_phone.S_phone SEPARATOR ',') ,supplier.city_name FROM Supplier INNER JOIN Supplier_phone on Supplier.S_ID=Supplier_phone.S_ID  GROUP BY Supplier.S_ID")
    #cur.execute("SELECT Supplier.S_ID, Supplier.S_name,Supplier.S_mail,Supplier.firm_no,Supplier.street_name,GROUP_CONCAT(DISTINCT Supplier_phone.S_phone SEPARATOR ',')  FROM Supplier INNER JOIN Supplier_phone on Supplier.S_ID=Supplier_phone.S_ID  GROUP BY Supplier.S_ID")
    data = cur.fetchall()
    cur.close()




    return render_template('supplier.html',supplier=data )

@app.route('/add_supplierdata', methods=['POST'])
def add_supplierdata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact_no']
        email = request.form['email']
        firm_no = request.form['firm_no']
        locality_name = request.form['locality_name']
        city = request.form['city']
        contact_list=contact.split(',')
        for i in range(len(contact_list)):
            result=cur.execute("Select supplier.S_ID FROM Supplier inner join supplier_phone on supplier.S_ID=supplier_phone.S_ID where supplier.s_mail= (%s) OR supplier_phone.S_phone=(%s)", (email,contact_list[i]))
        if result==0:
            cur.execute("INSERT INTO supplier(S_name, S_mail,street_name, firm_no,city_name) VALUES (%s,%s,%s,%s,%s)", (name, email, locality_name,firm_no,city))
            S_ID=cur.execute("Select S_ID FROM Supplier where s_mail= (%s)", (email,))
            S_ID=cur.fetchall()
            for i in range(len(contact_list)):
                cur.execute("INSERT INTO supplier_phone(S_ID,s_phone) VALUES (%s,%s)",(S_ID,contact_list[i]))
            mysql.connection.commit()
            cur.close()
            flash('Data Added successfully')
            return redirect(url_for('supplier'))
        else:
             flash('WrongEntry...Try Again!!!')
             return redirect(url_for('supplier'))      

@app.route('/updatesupplier/<id_data>', methods=['POST'])
def updatesupplier(id_data):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        contact = request.form['contact_no']
        email = request.form['email']
        firm_no = request.form['firm_no']
        locality_name = request.form['locality_name']
        city = request.form['city']
        contact_list=contact.split(',')
        for i in range(len(contact_list)):
            result=cur.execute("Select supplier.S_ID FROM Supplier inner join supplier_phone on supplier.S_ID=supplier_phone.S_ID where (supplier.s_mail= (%s) OR supplier_phone.S_phone=(%s)) AND supplier.S_ID<>(%s)", (email,contact_list[i],id_data))
        if result==0:
            cur.execute("""UPDATE supplier SET S_name=%s, S_mail=%s,street_name=%s, firm_no=%s,city_name=%s WHERE S_ID=%s""", (name, email, locality_name,firm_no,city,id_data))
            cur.execute("DELETE FROM supplier_phone WHERE S_ID=%s", (id_data,))
            for i in range(len(contact_list)):
                cur.execute("INSERT INTO supplier_phone(S_ID,s_phone) VALUES (%s,%s)",(id_data,contact_list[i]))
            mysql.connection.commit()
            flash('Data Updated successfully')
            return redirect(url_for('supplier'))
        else:
             flash('WrongEntry...Try Again!!!')
             return redirect(url_for('supplier')) 

@app.route('/deletesupplier/<string:id_data>', methods = ['GET'])
def deletesupplier(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM purchase WHERE S_ID=%s", (id_data,))
    cur.execute("DELETE FROM supplier_phone WHERE S_ID=%s", (id_data,))
    cur.execute("DELETE FROM supplier WHERE S_ID=%s", (id_data,))
    
    mysql.connection.commit()
    return redirect(url_for('supplier'))       


        # SUPPLIER END
       
@app.route('/search_supplierdata', methods=['POST'])
def search_supplierdata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name="%" + request.form['Name'] + "%"
        cur.execute(" SELECT Supplier.S_ID, Supplier.S_name,Supplier.S_mail,Supplier.firm_no,Supplier.street_name,GROUP_CONCAT(DISTINCT Supplier_phone.S_phone SEPARATOR ',') ,supplier.city_name FROM Supplier INNER JOIN Supplier_phone on Supplier.S_ID=Supplier_phone.S_ID group by supplier.S_ID having Supplier.S_name LIKE %s OR GROUP_CONCAT(DISTINCT Supplier_phone.S_phone SEPARATOR ',') like %s or  Supplier.S_mail LIKE %s OR Supplier.firm_no LIKE %s OR Supplier.street_name LIKE %s  OR supplier.city_name  LIKE %s  ORDER BY Supplier.S_ID",(name,name,name,name,name,name))
        data=cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('supplier.html',supplier=data) 



# PATIENT START
    
@app.route("/patient")
def patient():
    
    cur = mysql.connection.cursor()
    # cur.execute("SELECT  Supplier.S_name,Supplier.S_email,Supplier.firm_no,Supplier.street_name,Supplier_phone.S_phone  FROM Supplier LEFT JOIN Supplier_phone on Supplier.S_ID=Supplier_phone.S_ID ")
    cur.execute("SELECT Patient.P_ID, Patient.P_firstname,Patient.P_lastname,Patient.Presp_no,GROUP_CONCAT(DISTINCT patient_phone.patient_phone SEPARATOR ','),Patient.house_no,Patient.locality_name,Patient.city, Doctor.D_name  FROM Patient INNER JOIN Doctor ON  Patient.D_ID=Doctor.D_ID INNER JOIN patient_phone on patient_phone.P_ID=patient.P_ID GROUP BY Patient.P_ID ORDER BY Patient.P_ID DESC")
    #cur.execute("SELECT  Supplier.S_name,Supplier.S_email,Supplier.firm_no,Supplier.street_name,Supplier_zipcode.city_name  FROM Supplier  LEFT JOIN Supplier_zipcode on Supplier.zip_code=Supplier_zipcode.zip_code UNION ALL SELECT Supplier_phone.S_phone FROM Supplier LEFT JOIN Supplier_phone on Supplier.S_ID=Supplier_phone.S_ID")
    data = cur.fetchall()
    cur.close()
    return render_template('patient.html',patient=data) 

@app.route('/add_patientdata', methods=['POST'])
def add_patientdata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        P_firstname = request.form['firstname']
        P_lastname = request.form['lastname']
        Presp_no= request.form['prescription_no']
        doctorname= request.form['doctorname']
        house_no= request.form['house_no']
        locality_name= request.form['locality_name']
        city = request.form['city']
        phone = request.form['phone']
        cur.execute("select D_ID FROM Doctor where d_name= (%s)", (doctorname,))
        D_ID=cur.fetchall()
        contact_list=phone.split(',')
        result=cur.execute("Select patient.P_ID FROM patient inner join patient_phone on patient.P_ID=patient_phone.P_ID where patient.presp_no= (%s) ", (Presp_no,))
        if result==0:
            cur.execute("insert into Patient(Presp_no, P_firstname, P_lastname, house_no, locality_name, city, D_ID) values (%s,%s,%s,%s,%s,%s,%s)", ( Presp_no, P_firstname, P_lastname, house_no, locality_name, city, D_ID))
            cur.execute("Select P_ID FROM patient where presp_no=(%s)", (Presp_no,))
            id_data=cur.fetchall()
            for i in range(len(contact_list)):
                cur.execute("insert into patient_phone(P_ID,patient_phone) values (%s,%s)",(id_data,contact_list[i]))
            mysql.connection.commit()
            cur.close()
            flash('Patient Added successfully')
            return redirect(url_for('patient'))
        else:
             flash('WrongEntry Try Again')
             return redirect(url_for('patient')) 

@app.route('/updatepatient/<id_data>', methods=['POST'])
def updatepatient(id_data):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        P_firstname = request.form['firstname']
        P_lastname = request.form['lastname']
        Presp_no= request.form['prescription_no']
        doctorname= request.form['doctorname']
        house_no= request.form['house_no']
        locality_name= request.form['locality_name']
        city = request.form['city']
        phone = request.form['phone']
        contact_list=phone.split(',')
        result=cur.execute("Select patient.P_ID FROM patient inner join patient_phone on patient.P_ID=patient_phone.P_ID where (patient.presp_no= (%s) ) AND patient.P_ID<>(%s)", (Presp_no,id_data))
        if result==0:    
            cur.execute("DELETE FROM patient_phone WHERE P_ID=%s", (id_data,))
            cur.execute("select D_ID FROM Doctor where d_name= (%s)", (doctorname,))
            D_ID=cur.fetchall()
            cur.execute("""UPDATE Patient SET  Presp_no=%s, P_firstname=%s, P_lastname=%s, house_no=%s, locality_name=%s, city=%s,  D_ID=%s  where P_ID=%s""" , ( Presp_no, P_firstname, P_lastname, house_no, locality_name, city, D_ID,id_data))
            for i in range(len(contact_list)):
                cur.execute("INSERT INTO patient_phone(P_ID,patient_phone) VALUES (%s,%s)",(id_data,contact_list[i]))
            flash("Data Updated Successfully")
            mysql.connection.commit()
            return redirect(url_for('patient'))
        else:
            flash('WrongEntry Try Again')
            return redirect(url_for('patient')) 

@app.route('/deletepatient/<string:id_data>', methods = ['GET'])
def deletepatient(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM sales WHERE P_ID=%s", (id_data,))
    cur.execute("DELETE FROM patient_phone WHERE P_ID=%s", (id_data,))
    cur.execute("DELETE FROM Patient WHERE P_ID=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('patient'))       


    
     # PATIENT END

@app.route('/search_patientdata', methods=['POST'])
def search_patientdata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name="%" + request.form['Name'] + "%"
        name1=request.form['Name']
        cur.execute("SELECT Patient.P_ID, Patient.P_firstname,Patient.P_lastname,Patient.Presp_no,GROUP_CONCAT(DISTINCT patient_phone.patient_phone SEPARATOR ','),Patient.house_no,Patient.locality_name,Patient.city, Doctor.D_name  FROM Patient INNER JOIN Doctor ON  Patient.D_ID=Doctor.D_ID INNER JOIN patient_phone on patient_phone.P_ID=patient.P_ID GROUP BY Patient.P_ID   having Patient.P_firstname LIKE %s OR Patient.P_lastname LIKE %s OR Patient.Presp_no like %s OR GROUP_CONCAT(DISTINCT patient_phone.patient_phone SEPARATOR ',') like %s OR Doctor.D_name LIKE %s OR Patient.house_no LIKE %s or Patient.locality_name LIKE %s or Patient.city LIKE %s order by P_ID desc" ,(name,name,name1,name,name,name,name,name))
        data=cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('patient.html',patient=data) 


# MEDICINE START

@app.route("/medicine")
def medicine():
    cur = mysql.connection.cursor()
    cur.execute("SELECT M_ID,M_name,company_name,batch_no,mfg_date,expiry_date,quantity,selling_price,medicine_type from medicine ORDER BY M_ID desc")
    data=cur.fetchall()
    cur.close()
    return render_template('medicine.html',medicine=data)
    
@app.route('/add_medicinedata', methods=['POST'])
def add_medicinedata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        company = request.form['company']
        batch_no= request.form['batch_no']
        qty= request.form['qty']
        selling_price= request.form['selling_price']
        mfg= request.form['mfg']
        expiry= request.form['expiry']
        medicine_type= request.form['type']
        result=cur.execute("Select M_ID FROM Medicine where M_name= (%s) and batch_no=(%s)", (name,batch_no))
        if result==0:
            cur.execute("Insert into medicine(M_name,company_name,quantity,selling_price,mfg_date,expiry_date,batch_no,medicine_type) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(name,company,qty,selling_price,mfg,expiry,batch_no,medicine_type))
            mysql.connection.commit()
            cur.close()
            flash('Medicine Added successfully')
            return redirect(url_for('medicine'))
        else:
            flash('Medicine Entry Already There!')
            return redirect(url_for('medicine'))

@app.route('/updatemedicine/<id_data>', methods=['POST'])
def updatemedicine(id_data):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        company = request.form['company']
        batch_no= request.form['batch_no']
        qty= request.form['qty']
        selling_price= request.form['selling_price']
        mfg= request.form['mfg']
        expiry= request.form['expiry']
        medicine_type= request.form['type']
        result=cur.execute("Select M_ID FROM Medicine where M_name= (%s) and batch_no=(%s) and M_ID<>(%s)", (name,batch_no,id_data))
        if result==0:
            cur.execute(""" UPDATE medicine SET M_name=%s,company_name=%s,quantity=%s,selling_price=%s,mfg_date=%s,expiry_date=%s,batch_no=%s,medicine_type=%s where M_ID=%s""",(name,company,qty,selling_price,mfg,expiry,batch_no,medicine_type,id_data))
            flash("Data Updated Successfully")
            mysql.connection.commit()
            return redirect(url_for('medicine'))
        else:
            flash('Medicine Entry Already There!')
            return redirect(url_for('medicine'))    

@app.route('/deletemedicine/<string:id_data>', methods = ['GET'])
def deletemedicine(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM sales WHERE M_ID=%s", (id_data,))
    cur.execute("DELETE FROM purchase WHERE M_ID=%s", (id_data,))
    cur.execute("DELETE FROM medicine WHERE M_ID=%s", (id_data,))
    mysql.connection.commit()
    # flash('Record Deleted successfully')
    return redirect(url_for('medicine')) 

@app.route('/search_medicinedata', methods=['POST'])
def search_medicinedata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name="%" + request.form['Name'] + "%"
        name1=request.form['Name']
        cur.execute("SELECT M_ID,M_name,company_name,batch_no,mfg_date,expiry_date,quantity,selling_price,medicine_type from medicine where M_name like %s or company_name like %s or batch_no like %s or mfg_date like %s or expiry_date like %s or quantity like %s or selling_price like %s or medicine_type like %s ORDER BY M_ID desc",(name,name,name,name,name,name,name,name))
        data=cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('medicine.html',medicine=data) 

#PURCHASE START

@app.route("/purchase")
def purchase():
    cur = mysql.connection.cursor()
    cur.execute("SELECT purchase.purchase_id,medicine.M_name,medicine.batch_no,supplier.S_name,purchase.qty,purchase.free_qty,purchase.cost_price,purchase.bill_type,purchase.cost_price * purchase.qty,invoice_no,purchase.p_date from purchase INNER JOIN supplier on supplier.S_ID=purchase.S_ID INNER JOIN medicine on medicine.M_ID=purchase.M_ID ORDER BY purchase_id DESC")
    #cur.execute("SELECT purchase.purchase_id,supplier.S_name,purchase.qty,purchase.free_qty,purchase.cost_price,purchase.bill_type from purchase INNER JOIN supplier on supplier.S_ID=purchase.S_ID ")
    data=cur.fetchall()
    cur.close()
    return render_template('purchase.html',purchase=data)

@app.route('/add_purchasedata', methods=['POST'])
def add_purchasedata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name =  request.form['name'] 
        sname = request.form['sname']
        qty= request.form['qty']
        free_qty= request.form['freeqty']
        bill_type= request.form['billtype']
        p_date= request.form['pdate']
        cost_price = request.form['rate']
        invoice_no= request.form['invoiceno']
        batch_no=  request.form['batch_no']
        result=cur.execute("select * FROM medicine where M_name = (%s) AND batch_no = (%s)",(name,batch_no))
       
        if result==0:
            flash('Invalid Entry..Please Try Again!!')
            return redirect(url_for('purchase'))
        else:
            cur.execute("select S_ID FROM supplier where S_name=%s ",(sname,))
            S_ID=cur.fetchall()
            cur.execute("select M_ID FROM medicine where M_name LIKE (%s) AND batch_no LIKE (%s)",(name,batch_no))
            M_ID=cur.fetchall()
            cur.execute("INSERT INTO purchase(S_ID,M_ID,qty,free_qty,cost_price,p_date,bill_type,invoice_no,E_ID) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)", (S_ID,M_ID,qty,free_qty,cost_price,p_date,bill_type,invoice_no,'1'))
            cur.execute("INSERT INTO supplies(S_ID,M_ID) VALUES(%s,%s)",(S_ID,M_ID))
            mysql.connection.commit()
            cur.close()
            flash('Purchase Added successfully')
            return redirect(url_for('purchase'))

@app.route('/updatepurchase/<id_data>', methods=['POST'])
def updatepurchase(id_data):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name =  request.form['name'] 
        sname = request.form['sname']
        qty= request.form['qty']
        free_qty= request.form['freeqty']
        bill_type= request.form['billtype']
        p_date= request.form['pdate']
        cost_price = request.form['rate']
        invoice_no= request.form['invoiceno']
        batch_no=  request.form['batch_no'] 
        result=cur.execute("select * FROM medicine where M_name = (%s) AND batch_no = (%s)",(name,batch_no))
        if result==0:
            flash('Invalid Entry..Please Try Again!!!')
            return redirect(url_for('purchase'))
        else:
            cur.execute("select S_ID FROM supplier where S_name=%s ",(sname,))
            S_ID=cur.fetchall()
            cur.execute("select M_ID FROM medicine where M_name LIKE (%s) AND batch_no LIKE (%s)",(name,batch_no))
            M_ID=cur.fetchall()
            cur.execute("UPDATE purchase set S_ID=%s,M_ID=%s,qty=%s,free_qty=%s,cost_price=%s,p_date=%s,bill_type=%s,invoice_no=%s,E_ID=%s where purchase_id=%s",(S_ID,M_ID,qty,free_qty,cost_price,p_date,bill_type,invoice_no,'1',id_data))
            flash("Data Updated Successfully")
            mysql.connection.commit()
            return redirect(url_for('purchase'))

@app.route('/deletepurchase/<string:id_data>', methods = ['GET'])
def deletepurchase(id_data):
    cur = mysql.connection.cursor()
    M_ID=cur.execute("SELECT M_ID FROM  purchase WHERE purchase_id=%s", (id_data,))
    M_ID=cur.fetchall()
    
    cur.execute("DELETE FROM purchase WHERE purchase_id=%s", (id_data,))
    
    mysql.connection.commit()
    flash("Record Has Been Deleted Successfully")
    return redirect(url_for('purchase')) 

@app.route('/search_purchasedata', methods=['POST'])
def search_purchasedata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name="%" + request.form['Name'] + "%"
        cur.execute("SELECT purchase.purchase_id,medicine.M_name,medicine.batch_no,supplier.S_name,purchase.qty,purchase.free_qty,purchase.cost_price,purchase.bill_type,purchase.cost_price * purchase.qty,invoice_no,purchase.p_date from purchase INNER JOIN supplier on supplier.S_ID=purchase.S_ID INNER JOIN medicine on medicine.M_ID=purchase.M_ID  where medicine.M_name like %s OR medicine.batch_no like %s OR supplier.S_name LIKE %s OR purchase.invoice_no like %s OR purchase.p_date like %s or purchase.qty like %s or purchase.free_qty like %s or purchase.cost_price like %s or (purchase.cost_price*purchase.qty)like %s ORDER BY purchase_id DESC",(name,name,name,name,name,name,name,name,name))
        #cur.execute("SELECT purchase.purchase_id,medicine.M_name,medicine.batch_no,supplier.S_name,purchase.qty,purchase.free_qty,purchase.cost_price,purchase.bill_type,purchase.cost_price * purchase.qty,invoice_no,purchase.p_date from purchase INNER JOIN supplier on supplier.S_ID=purchase.S_ID INNER JOIN medicine on medicine.M_ID=purchase.M_ID where medicine.M_name like %s OR medicine.batch_no like %s OR supplier.s_name like %s or purchase.invoice_no like %s OR purchase.bill_type like %s OR purchase.p_date like %s order by purchase.purchase_id desc)",(name,name,name,name,name,name))
        data=cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('purchase.html',purchase=data) 


# PURCHASE END

# SALES START

@app.route("/sales")
def sales():
    cur = mysql.connection.cursor()
    cur.execute("SELECT sales.sales_id,medicine.M_name,medicine.batch_no,medicine.selling_price,patient.P_firstname,patient.presp_no,sales.s_qty,sales.bill_type,medicine.selling_price * sales.s_qty,sales.s_date,patient.P_lastname from sales INNER JOIN Patient on Patient.P_ID=sales.P_ID INNER JOIN medicine on medicine.M_ID=sales.M_ID ORDER BY sales_id DESC")
    # #cur.execute("SELECT purchase.purchase_id,supplier.S_name,purchase.qty,purchase.free_qty,purchase.cost_price,purchase.bill_type from purchase INNER JOIN supplier on supplier.S_ID=purchase.S_ID ")
    data=cur.fetchall()
    cur.close()
    return render_template('sales.html',sales=data,sales1=data)

@app.route('/add_salesdata', methods=['POST'])
def add_salesdata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name =  request.form['name'] 
        qty= request.form['qty']
        presp_no=request.form['presp_no']
        bill_type= request.form['billtype']
        s_date= request.form['sdate']
        batch_no= request.form['batch_no'] 
        result=cur.execute("select * FROM medicine where M_name = (%s) AND batch_no = (%s)",(name,batch_no))
        result1= cur.execute("select * FROM patient where presp_no=(%s) ",(presp_no,))
        if ((result==0) ):
            flash('Invalid Entry..Please Try Again!!')
            return redirect(url_for('sales'))
        else: 
            if ((result1==0) ):
                flash('Invalid Entry..Please Try Again!!')
                return redirect(url_for('sales'))   
            else:    
                cur.execute("select M_ID FROM medicine where M_name LIKE %s AND batch_no LIKE %s",(name,batch_no))
                M_ID=cur.fetchall()
                cur.execute("select sum(quantity) FROM medicine where M_name LIKE %s group by M_name",(name,))
                quantity=cur.fetchall()
                cur.execute("select P_ID FROM patient where presp_no=%s ",(presp_no,))
                P_ID=cur.fetchall()
                cur.execute("INSERT INTO sales(P_ID,M_ID,s_qty,s_date,bill_type,E_ID) VALUES (%s,%s,%s,%s,%s,%s)", (P_ID,M_ID,qty,s_date,bill_type,'1'))
                #cur.execute("INSERT INTO sales(P_ID,M_ID,s_qty,s_date,bill_type,sinvoice_no,E_ID) VALUES(%s,%s,%s,%s,%s,%s,%s)", (P_ID,M_ID,qty,s_date,bill_type,invoice_no,'1'))
                cur.execute("update medicine set quantity=quantity-" + qty + " where M_ID=%s",(M_ID,))
                mysql.connection.commit()
                cur.close()
                flash('Data Added successfully')

                return redirect(url_for('sales'))
   
@app.route('/updatesales/<id_data>', methods=['POST'])
def updatesales(id_data):
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name = request.form['name']
        qty= request.form['qty']
        presp_no=request.form['presp_no']
        bill_type= request.form['billtype']
        s_date= request.form['sdate']
        batch_no=  request.form['batch_no']
        result=cur.execute("select * FROM medicine where M_name = (%s) AND batch_no = (%s)",(name,batch_no))
        result1= cur.execute("select * FROM patient where presp_no=(%s) ",(presp_no,))
        if ((result==0) ):
            flash('Invalid Entry..Please Try Again!!')
            return redirect(url_for('sales'))
        else:    
            if ((result1==0) ):
                flash('Invalid Entry..Please Try Again!!')
                return redirect(url_for('sales'))
            else:    
                cur.execute("select M_ID FROM medicine where M_name LIKE %s AND batch_no LIKE %s",(name,batch_no))
                M_ID=cur.fetchall()
                cur.execute("select P_ID FROM patient where presp_no=%s ",(presp_no,))
                P_ID=cur.fetchall()
                cur.execute("update medicine,sales set medicine.quantity=medicine.quantity+sales.s_qty where medicine.M_ID=sales.M_ID and sales_id=%s ",(id_data,))
                cur.execute("update sales set M_ID=%s,P_ID=%s,s_qty=%s,s_date=%s,bill_type=%s,E_ID=%s where sales_id=%s",(M_ID,P_ID,qty,s_date,bill_type,'1',id_data))
                cur.execute("update medicine set quantity=quantity-" + qty + " where M_ID=%s",(M_ID,))
                flash("Data Updated Successfully")
                mysql.connection.commit()
                return redirect(url_for('sales'))

@app.route('/deletesales/<string:id_data>', methods = ['GET'])
def deletesales(id_data):
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("Select M_ID FROM sales WHERE sales_id=%s", (id_data,))
    M_ID=cur.fetchall()
    cur.execute("Select s_qty FROM sales WHERE sales_id=%s", (id_data,))
    s_qty=cur.fetchall()
    cur.execute("update medicine,sales set medicine.quantity=medicine.quantity+sales.s_qty where medicine.M_ID=sales.M_ID and sales_id=%s ",(id_data,))
    cur.execute("DELETE FROM sales WHERE sales_id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('sales')) 

@app.route('/search_salesdata', methods=['POST'])
def search_salesdata():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name="%" + request.form['Name'] + "%"
        cur.execute("SELECT sales.sales_id,medicine.M_name,medicine.batch_no,medicine.selling_price,patient.P_firstname,patient.presp_no,sales.s_qty,sales.bill_type,medicine.selling_price * sales.s_qty,sales.s_date,patient.P_lastname from sales INNER JOIN Patient on Patient.P_ID=sales.P_ID INNER JOIN medicine on medicine.M_ID=sales.M_ID where medicine.M_name like %s OR medicine.batch_no like %s OR patient.presp_no LIKE %s OR patient.P_firstname LIKE %s OR patient.P_lastname LIKE %s OR sales.s_date like %s OR  sales.s_qty like %s or sales.bill_type like %s or (medicine.selling_price * sales.s_qty) like %s  ORDER BY sales_id DESC",(name,name,name,name,name,name,name,name,name))
        data=cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('sales.html',sales=data) 


@app.route("/totalsales")
def totalsales():
    cur = mysql.connection.cursor()
    cur.execute("SELECT sales.s_date,sum(sales.s_qty),sum(medicine.selling_price * sales.s_qty) from sales inner join medicine on sales.M_ID=medicine.M_ID group by s_date order by s_date desc ")
    # #cur.execute("SELECT purchase.purchase_id,supplier.S_name,purchase.qty,purchase.free_qty,purchase.cost_price,purchase.bill_type from purchase INNER JOIN supplier on supplier.S_ID=purchase.S_ID ")
    data=cur.fetchall()
    cur.close()
    return render_template('totalsales.html',totalsales=data)

@app.route('/search_totalsales', methods=['POST'])
def search_totalsales():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name="%" + request.form['Name'] + "%"
        cur.execute("SELECT sales.s_date,sum(sales.s_qty),sum(medicine.selling_price * sales.s_qty) from sales inner join medicine on sales.M_ID=medicine.M_ID group by s_date having s_date like %s OR sum(sales.s_qty) like %s or sum(medicine.selling_price * sales.s_qty) like %s order by s_date desc",(name,name,name))
        data=cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('totalsales.html',totalsales=data) 

@app.route("/expired")
def expired():
    cur = mysql.connection.cursor()
    # cur.execute("DELETE FROM medicine where expiry_date<NOW()")
    cur.execute( "select curdate(),M_name,batch_no,quantity,mfg_date,expiry_date from medicine where expiry_date<=NOW()")
    data=cur.fetchall()
    
    cur.close()
    return render_template('expired.html',expiry=data) 

@app.route("/search_expired", methods=['POST'])
def search_expired():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name="%" + request.form['Name'] + "%"
        cur.execute( "select curdate(),M_name,batch_no,quantity,mfg_date,expiry_date from medicine where ((expiry_date<NOW()) AND(M_name like %s OR curdate() like %s OR batch_no LIKE %s OR quantity LIKE %s OR mfg_date LIKE %s or expiry_date like %s) )",(name,name,name,name,name,name))
        data=cur.fetchall()
        cur.close()
        return render_template('expired.html',expiry=data)     

@app.route("/reorder")
def reorder():
    cur = mysql.connection.cursor()
    cur.execute( "select curdate(),M_name,quantity from medicine where quantity<25 group by M_name")
    data=cur.fetchall()
    cur.close()
    return render_template('reorder.html',reorder=data)        

@app.route('/search_reorder', methods=['POST'])
def search_reorder():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        name="%" + request.form['Name'] + "%"
        cur.execute("SELECT curdate(),M_name,quantity from medicine where quantity<25 group by M_name having M_name like %s OR quantity like %s or curdate() like %s",(name,name,name))
        data=cur.fetchall()
        mysql.connection.commit()
        cur.close()
        return render_template('reorder.html',reorder=data) 

@app.route("/status")
def status():
    cur = mysql.connection.cursor()
    cur.execute("SELECT sum(medicine.selling_price * sales.s_qty) from sales inner join medicine on sales.M_ID=medicine.M_ID group by s_date having s_date=curdate() ")
    data1=cur.fetchall()
    cur.execute( "select count(*) from medicine where  expiry_date<=NOW()")
    data2=cur.fetchall()
    cur.execute( "select count(*) from medicine where quantity<25  ")
    data3=cur.fetchall()
    cur.close()
    return render_template('status.html',totalsales=data1,expire=data2,reorder=data3)

@app.route("/sales1")
def sales1():
   
    cur = mysql.connection.cursor()
    cur.execute("SELECT sales1.sales_id,sales1.s_date,sales1.s_invoice_no,sales1.bill_type,patient.presp_no,patient.P_firstname,patient.P_lastname,sum(sales_med.qty),sum(sales_med.qty*medicine.selling_price) from sales1 inner join patient on patient.P_ID=sales1.P_ID INNER JOIN sales_med on sales_med.sales_id=sales1.sales_id INNER JOIN medicine on  medicine.M_ID=sales_med.M_ID group by sales1.sales_id,sales1.s_invoice_no,sales1.bill_type,sales1.P_ID ORDER BY sales1.sales_id DESC")
    data=cur.fetchall()
    cur.close()
    return render_template('sales1.html',sales1=data)

@app.route('/add_sales1data', methods=['POST'])
def add_sales1data():
    cur = mysql.connection.cursor()
    if request.method == 'POST':
        presp_no=request.form['presp_no']
        bill_type= request.form['billtype']
        s_date= request.form['sdate']
        invoice_no= request.form['invoice_no']
        M_name=request.form.getlist('M_name[]')
        batch_no=request.form.getlist('batch_no[]')
        qty=request.form.getlist('qty[]')
        M_ID=[]
        for i in range(len(M_name)): 
           cur.execute("select M_ID FROM medicine where M_name LIKE %s AND batch_no LIKE %s",(M_name[i],batch_no[i]))
           Med_ID=cur.fetchall()
           M_ID.append(Med_ID)
        cur.execute("select P_ID FROM patient where presp_no=%s ",(presp_no,))
        P_ID=cur.fetchall()
        cur.execute("INSERT INTO sales1(P_ID,s_date,bill_type,s_invoice_no,E_ID) VALUES (%s,%s,%s,%s,%s)", (P_ID,s_date,bill_type,invoice_no,'1'))
        cur.execute("Select sales_id from sales1 where s_invoice_no like %s ",(invoice_no,))
        sales_id=cur.fetchall()
        for i in range(len(M_ID)): 
           cur.execute("INSERT INTO sales_med(sales_id,M_ID,qty)values(%s,%s,%s)",(sales_id,M_ID[i],qty[i]))
        mysql.connection.commit()
        cur.close()
        flash('Data Added successfully')
        return redirect(url_for('sales1'))

@app.route('/edit_sales1data/<id_data>')
def edit_sales1data(id_data):
    cur = mysql.connection.cursor()
    cur.execute("SELECT sales1.sales_id,sales1.s_date,sales1.s_invoice_no,sales1.bill_type,patient.presp_no,patient.P_firstname,patient.P_lastname from sales1 inner join patient on patient.P_ID=sales1.P_ID where sales1.sales_id=%s",(id_data,))
    data=cur.fetchall()
    cur.close()
    return (render_template('sales1.html',data=data))    



if __name__ == '__main__':
    app.run(debug=True)