       IDENTIFICATION DIVISION.
       PROGRAM-ID. CB109-TRANSACTION-VALIDATOR.
       AUTHOR. LEGACY-SYSTEMS-TEAM.
       DATE-WRITTEN. 1998-03-15.
      *================================================================
      * CB109 - CREDIT CARD TRANSACTION VALIDATION MODULE
      * This module validates credit card transactions against
      * account limits and promotional eligibility rules.
      *================================================================

       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.

       DATA DIVISION.
       WORKING-STORAGE SECTION.

       01  WS-ACCOUNT-RECORD.
           05  ACCT-NUMBER           PIC X(16).
           05  ACCT-CREDIT-LIMIT     PIC S9(7)V99
                                     PACKED-DECIMAL.
           05  ACCT-CURRENT-BALANCE  PIC S9(7)V99
                                     PACKED-DECIMAL.
           05  ACCT-AVAILABLE-CREDIT PIC S9(7)V99
                                     PACKED-DECIMAL.
           05  ACCT-STATUS           PIC X(2).
               88  ACCT-ACTIVE       VALUE 'AC'.
               88  ACCT-SUSPENDED    VALUE 'SU'.
               88  ACCT-CLOSED       VALUE 'CL'.

       01  WS-TRANSACTION-RECORD.
           05  TXN-ID               PIC X(12).
           05  TXN-AMOUNT           PIC S9(7)V99
                                    PACKED-DECIMAL.
           05  TXN-MERCHANT-CODE    PIC X(6).
           05  TXN-CATEGORY         PIC X(10).
           05  TXN-TIMESTAMP        PIC X(26).

       01  WS-PROMO-RECORD.
           05  PROMO-CODE           PIC X(8).
           05  PROMO-ACTIVE-FLAG    PIC X(1).
               88  PROMO-IS-ACTIVE  VALUE 'Y'.
               88  PROMO-INACTIVE   VALUE 'N'.
           05  PROMO-PRODUCT-TYPE   PIC X(12).
           05  PROMO-DISCOUNT-PCT   PIC S9(3)V99
                                    PACKED-DECIMAL.

       01  WS-DECISION-FIELDS.
           05  WS-TEMP-BALANCE      PIC S9(7)V99
                                    PACKED-DECIMAL.
           05  WS-DECLINE-FLAG      PIC X(1).
               88  DECLINE-TRUE     VALUE 'Y'.
               88  DECLINE-FALSE    VALUE 'N'.
           05  WS-DECISION-REASON   PIC X(40).

       PROCEDURE DIVISION.

       MAIN-PROCESS.
           PERFORM INIT-FIELDS
           PERFORM VALIDATE-TRANSACTION
           PERFORM CHECK-PROMO-ELIGIBILITY
           PERFORM RECORD-DECISION
           STOP RUN.

      *================================================================
      * INIT-FIELDS: Initialize working storage fields
      *================================================================
       INIT-FIELDS.
           MOVE SPACES TO WS-DECISION-REASON
           MOVE 'N' TO WS-DECLINE-FLAG
           COMPUTE WS-TEMP-BALANCE =
               ACCT-CURRENT-BALANCE + TXN-AMOUNT
           .

      *================================================================
      * VALIDATE-TRANSACTION: Core transaction validation
      * RULE: CB109-R3
      * Lines 340-355: Credit limit check
      *================================================================
       VALIDATE-TRANSACTION.
      *--- CB109-R3: CREDIT LIMIT VALIDATION RULE ---
      *--- If the projected balance exceeds the credit limit,
      *--- decline the transaction immediately.
           IF WS-TEMP-BALANCE > ACCT-CREDIT-LIMIT
               MOVE 'Y' TO WS-DECLINE-FLAG
               MOVE 'OVER_CREDIT_LIMIT' TO WS-DECISION-REASON
               PERFORM LOG-DECLINE
           END-IF
           .

      *================================================================
      * CHECK-PROMO-ELIGIBILITY: Promotional offer validation
      * RULE: CB109-R5
      *================================================================
       CHECK-PROMO-ELIGIBILITY.
           IF PROMO-IS-ACTIVE
               IF TXN-CATEGORY = 'Travel'
                   CONTINUE
               ELSE
                   MOVE 'N' TO PROMO-ACTIVE-FLAG
               END-IF
           END-IF
           .

      *================================================================
      * LOG-DECLINE: Write decline to audit log
      *================================================================
       LOG-DECLINE.
           DISPLAY 'DECLINE: ' TXN-ID
                   ' REASON: ' WS-DECISION-REASON
           .

      *================================================================
      * RECORD-DECISION: Write immutable decision record
      *================================================================
       RECORD-DECISION.
           DISPLAY 'DECISION_ID: ' TXN-ID
           DISPLAY 'TIMESTAMP: ' TXN-TIMESTAMP
           DISPLAY 'RULE: CB109-R3'
           DISPLAY 'OUTCOME: ' WS-DECLINE-FLAG
           .
