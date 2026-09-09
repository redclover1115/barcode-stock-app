function doPost(e) {
  try {
    var params = JSON.parse(e.postData.contents);
    var janCode = String(params.janCode).trim();
    var category = params.status; 
    var inputCount = Number(params.count); 
    var userName = params.user || "未入力";
    var action = params.action || "register";
    var forceHeader = params.forceHeader || false; 
    
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // C列（JANコード）の最終行を正確に取得
    var cValues = sheet.getRange("C1:C").getValues();
    var lastRow = 0;
    for (var r = cValues.length - 1; r >= 0; r--) {
      if (cValues[r] !== "") { lastRow = r + 1; break; }
    }
    if (lastRow < 2) lastRow = 2;
    
    var janFinder = sheet.getRange(1, 3, lastRow, 1).createTextFinder(janCode).matchEntireCell(true).matchFormulaText(false).findNext();
    if (!janFinder) {
      return ContentService.createTextOutput(JSON.stringify({"status": "not_found", "message": "JANコードが見つかりません。"}));
    }
    
    var row = janFinder.getRow();
    var today = new Date();
    var formattedDate = Utilities.formatDate(today, "Asia/Tokyo", "yyyy/MM/dd HH:mm:ss");
    var logText = formattedDate + " " + userName;
    
    // 7工程の列マッピング（E列=5 から 2列おき）
    var pipeline = [
      { name: "棹カット", col: 5 },      // E列
      { name: "枠組み", col: 7 },        // G列
      { name: "スペーサー加工", col: 9 },  // I列
      { name: "中身セット", col: 11 },    // K列
      { name: "金具打ち", col: 13 },      // M列
      { name: "仕上げ", col: 15 },        // O列
      { name: "完成", col: 17 }           // Q列
    ];
    
    var currentIdx = pipeline.findIndex(function(p) { return p.name === category; });
    var currentCol = pipeline[currentIdx].col;
    
    // ーーー ジャンプ対応：前工程の自動クリア ーーー
    var prevCol = 0;
    var prevCategoryName = "";
    var prevCellVal = 0;
    
    if (action === "register") {
      for (var i = currentIdx - 1; i >= 0; i--) {
        var checkVal = Number(sheet.getRange(row, pipeline[i].col).getValue()) || 0;
        if (checkVal > 0) {
          prevCol = pipeline[i].col;
          prevCategoryName = pipeline[i].name;
          prevCellVal = checkVal;
          break; 
        }
      }
      
      // 不一致チェック
      if (prevCol > 0) {
        if (prevCellVal !== inputCount && !forceHeader) {
          return ContentService.createTextOutput(JSON.stringify({
            "status": "qty_mismatch",
            "message": "※前工程からの数が合いません。",
            "itemName": sheet.getRange(row, 2).getValue() ? String(sheet.getRange(row, 2).getValue()).trim() : "商品名未設定",
            "details": { "prevStatus": prevCategoryName, "prevCount": prevCellVal, "inputCount": inputCount }
          }));
        }
        if (prevCellVal === inputCount || forceHeader) {
          sheet.getRange(row, prevCol).setValue(0);
          sheet.getRange(row, prevCol + 1).setValue(logText + " (次工程へスキップ完了)");
        }
      }
    }
    
    // 今工程への加算・上書き
    if (currentCol > 0) {
      if (action === "register") {
        var currentCellVal = Number(sheet.getRange(row, currentCol).getValue()) || 0;
        sheet.getRange(row, currentCol).setValue(currentCellVal + inputCount);
        sheet.getRange(row, currentCol + 1).setValue(logText);
      } else if (action === "modify") {
        sheet.getRange(row, currentCol).setValue(inputCount);
        sheet.getRange(row, currentCol + 1).setValue(logText);
      }
    }
    
    // 最新データの個別集計（安全な番地直接参照）
    var itemName = sheet.getRange(row, 2).getValue() ? String(sheet.getRange(row, 2).getValue()).trim() : "商品名未設定";
    var itemStockData = {
      "katto": Number(sheet.getRange(row, 5).getValue()) || 0,
      "wakugumi": Number(sheet.getRange(row, 7).getValue()) || 0,
      "spacer": Number(sheet.getRange(row, 9).getValue()) || 0,
      "nakami": Number(sheet.getRange(row, 11).getValue()) || 0,
      "kanagu": Number(sheet.getRange(row, 13).getValue()) || 0,
      "shiage": Number(sheet.getRange(row, 15).getValue()) || 0,
      "kanryo": Number(sheet.getRange(row, 17).getValue()) || 0
    };
    
    // 全体合計の計算（エラー回避のため、1行ずつセルの値を確実に数値化して加算する安全設計に変更）
    var tKatto = 0, tWaku = 0, tSpace = 0, tNakami = 0, tKanagu = 0, tShiage = 0, tKanryo = 0;
    if (lastRow >= 2) {
      var allData = sheet.getRange(2, 5, lastRow - 1, 13).getValues(); 
      for (var i = 0; i < allData.length; i++) {
        // データの有無を厳密にチェックし、配列オブジェクトエラーを完全に防止
        if (allData[i] && allData[i].length >= 13) {
          tKatto  += (Number(allData[i][0]) || 0);  // E列
          tWaku   += (Number(allData[i][2]) || 0);  // G列
          tSpace  += (Number(allData[i][4]) || 0);  // I列
          tNakami += (Number(allData[i][6]) || 0);  // K列
          tKanagu += (Number(allData[i][8]) || 0);  // M列
          tShiage += (Number(allData[i][10]) || 0); // O列
          tKanryo += (Number(allData[i][12]) || 0); // Q列
        }
      }
    }
    
    var grandTotal = tKatto + tWaku + tSpace + tNakami + tKanagu + tShiage + tKanryo;
    var grandTotalData = {
      "katto": tKatto, "waku": tWaku, "spacer": tSpace, "nakami": tNakami, "kanagu": tKanagu, "shiage": tShiage, "kanryo": tKanryo, "grandTotal": grandTotal
    };
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success", "itemName": itemName, "stockData": itemStockData, "grandTotalData": grandTotalData
    }));
    
  } catch(error) {
    return ContentService.createTextOutput(JSON.stringify({"status": "error", "message": error.toString()}));
  }
}
