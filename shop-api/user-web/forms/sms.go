package forms

type SmsForm struct {
	Mobile string `form:"mobile" json:"mobile" binding:"required,mobile"`
	Type   string `form:"type" json:"type" binding:"required,oneof=register"`
}
