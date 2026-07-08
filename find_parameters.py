from hdbcli import dbapi

# 1. Insert your Cube.js .env credentials here
DB_HOST = "72669aac-4242-411a-9f61-501cada8b885.hana.prod-ap11.hanacloud.ondemand.com"
DB_PORT = 443 # Replace with your integer port
DB_USER = "WFMSCH_1_0TQI5KK6I07CS9JDOY924CJ0F_RT"
DB_PASS = "Uu4-FwgO0-BJ.Ez_xSaDpgIt0JtOcpN8u5Cj7miuMlMaknC4IMJM3Bso43SvuUvFb02x20ckApzCx.3-VBtidt2z-6a.vS6YSQdTyiwq7OPKZb5uKxxwiD39hfmC8j7."

def discover_hana_parameters():
    print("Connecting to SAP HANA...")
    try:
        conn = dbapi.connect(
            address=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS
        )
        cursor = conn.cursor()
        
        # 2. The Discovery SQL
        sql = """
        SELECT 
            'VIEW' AS OBJECT_TYPE, 
            SCHEMA_NAME, 
            VIEW_NAME AS OBJECT_NAME, 
            PARAMETER_NAME, 
            DATA_TYPE_NAME 
        FROM SYS.VIEW_PARAMETERS 
        WHERE VIEW_NAME LIKE '%V_ROSTER_PLANNED_EMP%'
        UNION ALL
        SELECT 
            'FUNCTION' AS OBJECT_TYPE, 
            SCHEMA_NAME, 
            FUNCTION_NAME AS OBJECT_NAME, 
            PARAMETER_NAME, 
            DATA_TYPE_NAME 
        FROM SYS.FUNCTION_PARAMETERS 
        WHERE FUNCTION_NAME LIKE '%V_ROSTER_PLANNED_EMP%';
        """
        
        cursor.execute(sql)
        results = cursor.fetchall()
        
        print("\n=== DISCOVERY RESULTS ===")
        if not results:
            print("No parameters found for this view.")
        else:
            for row in results:
                print(f"Type: {row[0]} | Schema: {row[1]} | Object: {row[2]}")
                print(f"-> PARAMETER_NAME: {row[3]}")
                print(f"-> DATA_TYPE: {row[4]}\n")
                
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"\nConnection Failed: {e}")
        print("Ensure you have 'hdbcli' installed (pip install hdbcli)")

if __name__ == "__main__":
    discover_hana_parameters()


